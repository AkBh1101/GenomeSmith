#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <unordered_map>
#include <unordered_set>
#include <stack>
#include <queue>
#include <algorithm>
#include <numeric>
#include <iomanip>
#include <chrono>
#include <filesystem>

using namespace std;
using namespace chrono;

/* =========================================================
   STOPWATCH UTILITY
   ========================================================= */
struct Stopwatch {
    time_point<high_resolution_clock> begin;
    void reset() { begin = high_resolution_clock::now(); }
    double elapsed_ms() const {
        return duration<double, milli>(high_resolution_clock::now() - begin).count();
    }
};

/* =========================================================
   COMPLEMENT UTILS
   canonical form = lexicographic min of (kmer, its reverse complement)
   ensures strands are handled symmetrically
   ========================================================= */
char complement_base(char b) {
    if (b == 'A') return 'T';
    if (b == 'T') return 'A';
    if (b == 'C') return 'G';
    return 'C';
}

string reverse_complement(const string& seq) {
    int len = (int)seq.size();
    string rc(len, ' ');
    for (int i = 0; i < len; ++i)
        rc[i] = complement_base(seq[len - 1 - i]);
    return rc;
}

/* =========================================================
   POLYNOMIAL ROLLING HASH — O(1) per window slide
   Uses Mersenne prime 2^61-1 and __uint128_t arithmetic
   ========================================================= */
namespace HashConfig {
    constexpr uint64_t RADIX = 5;
    constexpr uint64_t PRIME = (1ULL << 61) - 1;
}

uint64_t base_encode(char c) {
    switch (c) {
        case 'A': return 1; case 'C': return 2;
        case 'G': return 3; case 'T': return 4;
    }
    return 1;
}

uint64_t mod_mul(uint64_t x, uint64_t y) {
    return (__uint128_t)x * y % HashConfig::PRIME;
}

struct KmerHasher {
    int window;
    uint64_t cur_hash = 0, lead_pow = 1;

    explicit KmerHasher(int w) : window(w) {}

    void initialize(const string& s, int offset) {
        cur_hash = 0; lead_pow = 1;
        for (int i = 0; i < window; ++i) {
            cur_hash = (mod_mul(cur_hash, HashConfig::RADIX) + base_encode(s[offset + i])) % HashConfig::PRIME;
            if (i < window - 1)
                lead_pow = mod_mul(lead_pow, HashConfig::RADIX);
        }
    }

    void advance(char drop, char add) {
        cur_hash = (cur_hash + HashConfig::PRIME - mod_mul(lead_pow, base_encode(drop))) % HashConfig::PRIME;
        cur_hash = (mod_mul(cur_hash, HashConfig::RADIX) + base_encode(add)) % HashConfig::PRIME;
    }

    uint64_t get() const { return cur_hash; }
};

/* =========================================================
   PROBABILISTIC SET — Bloom Filter
   Two-pass scheme: add to real graph only if hash seen 2+ times
   ~8MB footprint, 3 hash functions
   ========================================================= */
struct ProbSet {
    static constexpr size_t N_BITS = 1ULL << 26;
    vector<uint8_t> bits;
    int num_fns;

    explicit ProbSet(int fns = 3) : bits(N_BITS / 8, 0), num_fns(fns) {}

    size_t probe(size_t h, int fn) const {
        uint64_t salt = (uint64_t)fn * 2654435761ULL;
        return ((h ^ salt) * 6364136223846793005ULL + 1442695040888963407ULL) % N_BITS;
    }

    void add(size_t h) {
        for (int i = 0; i < num_fns; ++i) {
            size_t p = probe(h, i);
            bits[p / 8] |= (1u << (p % 8));
        }
    }

    bool contains(size_t h) const {
        for (int i = 0; i < num_fns; ++i) {
            size_t p = probe(h, i);
            if (!(bits[p / 8] & (1u << (p % 8)))) return false;
        }
        return true;
    }
};

/* =========================================================
   DE BRUIJN GRAPH
   Nodes  = (k-1)-mers
   Edges  = k-mers
   Tracks per-edge frequency for coverage-weighted traversal
   ========================================================= */
struct DBGraph {
    unordered_map<string, vector<string>> neighbors;
    unordered_map<string, int> in_count, out_count;
    unordered_map<string, int> freq_map;   // "u->v" -> support count

    void insert_edge(const string& from, const string& to) {
        string eid = from + "->" + to;
        if (freq_map[eid]++ == 0) {
            neighbors[from].push_back(to);
            out_count[from]++;
            in_count[to]++;
            if (!in_count.count(from))   in_count[from]  = 0;
            if (!out_count.count(to))    out_count[to]   = 0;
            if (!neighbors.count(to))    neighbors[to];
        }
    }

    string eulerian_source() const {
        string fallback;
        for (auto& [n, od] : out_count) {
            int id = in_count.count(n) ? in_count.at(n) : 0;
            if (od - id == 1) return n;
            if (fallback.empty() && od > 0) fallback = n;
        }
        return fallback;
    }

    string eulerian_sink() const {
        string fallback;
        for (auto& [n, id] : in_count) {
            int od = out_count.count(n) ? out_count.at(n) : 0;
            if (id - od == 1) return n;
            if (fallback.empty() && od == 0 && id > 0) fallback = n;
        }
        return fallback;
    }

    size_t node_count() const { return neighbors.size(); }
    size_t edge_count() const {
        size_t total = 0;
        for (auto& [n, nb] : neighbors) total += nb.size();
        return total;
    }
};

/* =========================================================
   EULERIAN PATH — Hierholzer's algorithm  O(E)
   Each edge traversed exactly once
   ========================================================= */
vector<string> find_euler_path(DBGraph& dg) {
    string origin = dg.eulerian_source();
    if (origin.empty()) return {};

    unordered_map<string, int> ptr;
    for (auto& [n, _] : dg.neighbors) ptr[n] = 0;

    vector<string> trail;
    stack<string> call_stack;
    call_stack.push(origin);

    while (!call_stack.empty()) {
        string node = call_stack.top();
        auto& adj = dg.neighbors[node];
        if (ptr[node] < (int)adj.size())
            call_stack.push(adj[ptr[node]++]);
        else {
            trail.push_back(node);
            call_stack.pop();
        }
    }
    reverse(trail.begin(), trail.end());
    return trail;
}

/* =========================================================
   COVERAGE-WEIGHTED SHORTEST PATH — Dijkstra  O((V+E) log V)
   Edge cost = (max_freq + 1) - observed_freq
   Low cost → high coverage → preferred path
   ========================================================= */
string coverage_path_assemble(const DBGraph& dg) {
    if (dg.neighbors.empty()) return "";

    int peak_freq = 1;
    for (auto& [eid, f] : dg.freq_map)
        peak_freq = max(peak_freq, f);

    string src  = dg.eulerian_source();
    string dest = dg.eulerian_sink();
    if (src.empty()) return "";

    using PQEntry = pair<double, string>;
    priority_queue<PQEntry, vector<PQEntry>, greater<PQEntry>> heap;

    unordered_map<string, double> cost;
    unordered_map<string, string> came_from;
    unordered_map<string, int>    depth;

    for (auto& [n, _] : dg.neighbors) cost[n] = 1e18;
    cost[src]  = 0.0;
    depth[src] = 0;
    heap.push({0.0, src});

    while (!heap.empty()) {
        auto [d, u] = heap.top(); heap.pop();
        if (d > cost[u] + 1e-9) continue;

        for (auto& v : dg.neighbors.at(u)) {
            string eid = u + "->" + v;
            int fr = dg.freq_map.count(eid) ? dg.freq_map.at(eid) : 1;
            double w = double(peak_freq + 1 - fr);
            double nd = d + w;
            if (nd < cost[v] - 1e-9) {
                cost[v]      = nd;
                came_from[v] = u;
                depth[v]     = depth.count(u) ? depth[u] + 1 : 1;
                heap.push({nd, v});
            }
        }
    }

    string endpoint;
    if (!dest.empty() && cost.count(dest) && cost[dest] < 1e17) {
        endpoint = dest;
    } else {
        int best = 0;
        for (auto& [n, d] : depth) {
            if (n == src) continue;
            if (cost[n] < 1e17 && d > best) { best = d; endpoint = n; }
        }
    }
    if (endpoint.empty()) return src;

    vector<string> route;
    for (string cur = endpoint; ; cur = came_from[cur]) {
        route.push_back(cur);
        if (!came_from.count(cur)) break;
    }
    reverse(route.begin(), route.end());

    string assembled = route[0];
    for (size_t i = 1; i < route.size(); ++i)
        assembled += route[i].back();
    return assembled;
}

/* =========================================================
   GREEDY FALLBACK — picks highest-frequency unvisited edge
   ========================================================= */
string greedy_path_assemble(DBGraph& dg) {
    string pos = dg.eulerian_source();
    if (pos.empty()) return "";
    string result = pos;
    unordered_map<string, int> visited;
    while (true) {
        string best_next; int top_freq = -1;
        for (auto& nxt : dg.neighbors[pos]) {
            string eid = pos + "->" + nxt;
            if (!visited[eid]) {
                int f = dg.freq_map.count(eid) ? dg.freq_map.at(eid) : 1;
                if (f > top_freq) { top_freq = f; best_next = nxt; }
            }
        }
        if (best_next.empty()) break;
        visited[pos + "->" + best_next]++;
        result += best_next.back();
        pos = best_next;
    }
    return result;
}

/* =========================================================
   SINGLE-PASS ERROR SMOOTHER — O(N)
   Corrects isolated substitution errors via neighbour agreement
   ========================================================= */
string smooth_sequence(const string& raw) {
    string out = raw;
    for (int i = 1; i + 1 < (int)raw.size(); ++i) {
        if (raw[i - 1] == raw[i + 1] && raw[i] != raw[i - 1])
            out[i] = raw[i - 1];
    }
    return out;
}

/* =========================================================
   SEQUENCE STATISTICS
   ========================================================= */
double compute_gc(const string& s) {
    if (s.empty()) return 0.0;
    int count = 0;
    for (char c : s) if (c == 'G' || c == 'C') count++;
    return 100.0 * count / (double)s.size();
}

long long compute_n50(const string& assembly) {
    vector<long long> ctgs;
    long long run = 0;
    for (char c : assembly) {
        if (c == 'N') { if (run > 0) ctgs.push_back(run); run = 0; }
        else run++;
    }
    if (run > 0) ctgs.push_back(run);
    if (ctgs.empty()) return 0;

    sort(ctgs.rbegin(), ctgs.rend());
    long long total = 0;
    for (auto l : ctgs) total += l;
    long long half = total / 2, acc = 0;
    for (auto l : ctgs) { acc += l; if (acc >= half) return l; }
    return ctgs.back();
}

/* =========================================================
   SUFFIX ARRAY — prefix doubling  O(n log² n)
   Rank-based sort with early termination on unique ranks
   ========================================================= */
vector<int> suffix_array(const string& s) {
    int n = (int)s.size();
    if (n == 0) return {};

    vector<int> order(n), rnk(n), aux(n);
    iota(order.begin(), order.end(), 0);
    for (int i = 0; i < n; ++i) rnk[i] = (unsigned char)s[i];

    for (int gap = 1; gap < n; gap <<= 1) {
        auto cmp = [&](int a, int b) {
            if (rnk[a] != rnk[b]) return rnk[a] < rnk[b];
            int ra = (a + gap < n) ? rnk[a + gap] : -1;
            int rb = (b + gap < n) ? rnk[b + gap] : -1;
            return ra < rb;
        };
        sort(order.begin(), order.end(), cmp);

        aux[order[0]] = 0;
        for (int i = 1; i < n; ++i)
            aux[order[i]] = aux[order[i - 1]] + (cmp(order[i - 1], order[i]) ? 1 : 0);
        rnk = aux;
        if (rnk[order[n - 1]] == n - 1) break;
    }
    return order;
}

/* =========================================================
   LCP ARRAY — Kasai  O(n)
   Extends each match using the rank of the previous suffix
   ========================================================= */
vector<int> lcp_array(const string& s, const vector<int>& sa) {
    int n = (int)s.size();
    vector<int> inv(n), lcp(n, 0);
    for (int i = 0; i < n; ++i) inv[sa[i]] = i;

    for (int i = 0, h = 0; i < n; ++i) {
        if (inv[i] > 0) {
            int j = sa[inv[i] - 1];
            while (i + h < n && j + h < n && s[i + h] == s[j + h]) h++;
            lcp[inv[i]] = h;
            if (h > 0) h--;
        }
    }
    return lcp;
}

/* =========================================================
   REPEAT REGION STRUCTURE
   ========================================================= */
struct RepeatEntry {
    string  motif;
    int     span;
    int     count;
    vector<int> locs;
};

/* =========================================================
   REPEAT DETECTION — LCP-based grouping
   Consecutive SA entries with LCP >= threshold share a prefix
   ========================================================= */
vector<RepeatEntry> detect_repeats(const string& s,
                                    const vector<int>& sa,
                                    const vector<int>& lcp,
                                    int threshold = 20) {
    int n = (int)sa.size();
    int slen = (int)s.size();
    vector<RepeatEntry> found;

    int i = 1;
    while (i < n) {
        if (lcp[i] >= threshold) {
            int j = i, min_lcp = lcp[i];
            while (j < n && lcp[j] >= threshold) {
                min_lcp = min(min_lcp, lcp[j]);
                j++;
            }
            auto ok = [&](int p) { return p + min_lcp <= slen; };
            vector<int> positions;
            if (ok(sa[i - 1])) positions.push_back(sa[i - 1]);
            for (int x = i; x < j; ++x)
                if (ok(sa[x])) positions.push_back(sa[x]);

            if ((int)positions.size() >= 2) {
                string m = s.substr(positions[0], min_lcp);
                found.push_back({m, min_lcp, (int)positions.size(), positions});
            }
            i = j;
        } else {
            i++;
        }
    }
    sort(found.begin(), found.end(),
         [](const RepeatEntry& a, const RepeatEntry& b) {
             return a.span > b.span;
         });
    return found;
}

/* =========================================================
   FASTQ PARSER — sequence lines only  O(N)
   Normalises non-ACGT bases to 'A'
   ========================================================= */
vector<string> load_fastq(const string& filepath, long long& read_count) {
    ifstream fin(filepath);
    if (!fin) { cerr << "Cannot open " << filepath << "\n"; return {}; }
    vector<string> seqs;
    string line; int line_no = 0;
    while (getline(fin, line)) {
        if (line_no % 4 == 1) {
            string clean; clean.reserve(line.size());
            for (char c : line) {
                char u = toupper(c);
                clean += (u == 'A' || u == 'C' || u == 'G' || u == 'T') ? u : 'A';
            }
            if (!clean.empty()) seqs.push_back(move(clean));
        }
        ++line_no;
    }
    read_count = (long long)seqs.size();
    return seqs;
}

/* =========================================================
   JSON SERIALISER — graph export (no external deps)
   ========================================================= */
string json_str(const string& s) {
    string o; o.reserve(s.size() + 2);
    o += '"';
    for (char c : s) {
        if      (c == '"')  o += "\\\"";
        else if (c == '\\') o += "\\\\";
        else                o += c;
    }
    o += '"';
    return o;
}

void export_graph_json(const string& outpath, const DBGraph& dg) {
    const int NODE_CAP = 500, EDGE_CAP = 2000;
    ofstream fout(outpath);
    fout << "{\n  \"nodes\": [\n";

    unordered_set<string> node_set;
    for (auto& [n, _] : dg.neighbors) node_set.insert(n);
    vector<string> node_list(node_set.begin(), node_set.end());
    if ((int)node_list.size() > NODE_CAP) node_list.resize(NODE_CAP);

    for (size_t i = 0; i < node_list.size(); ++i) {
        fout << "    " << json_str(node_list[i]);
        if (i + 1 < node_list.size()) fout << ",";
        fout << "\n";
    }
    fout << "  ],\n  \"edges\": [\n";

    int ec = 0; bool first = true;
    for (auto& [u, nbrs] : dg.neighbors) {
        for (auto& v : nbrs) {
            if (ec++ >= EDGE_CAP) goto end_edges;
            string eid = u + "->" + v;
            int fr = dg.freq_map.count(eid) ? dg.freq_map.at(eid) : 1;
            if (!first) fout << ",\n";
            fout << "    {\"from\":" << json_str(u)
                 << ",\"to\":"       << json_str(v)
                 << ",\"weight\":"   << fr << "}";
            first = false;
        }
    }
    end_edges:
    fout << "\n  ],\n";
    fout << "  \"total_nodes\": " << dg.node_count() << ",\n";
    fout << "  \"total_edges\": " << dg.edge_count() << "\n}\n";
}

/* =========================================================
   REPEAT REPORT WRITER
   ========================================================= */
void write_repeat_file(const string& outpath,
                        const vector<RepeatEntry>& reps,
                        const string& assembly,
                        int threshold) {
    ofstream fout(outpath);
    fout << "GenomeSmith — Repeat Analysis Report\n";
    fout << string(60, '=') << "\n";
    fout << "Assembly length : " << assembly.size() << " bp\n";
    fout << "Min repeat len  : " << threshold       << " bp\n";
    fout << "Repeats found   : " << reps.size()     << "\n\n";

    int limit = min((int)reps.size(), 25);
    if (limit == 0) { fout << "No repeats found at this threshold.\n"; return; }

    fout << "Top " << limit << " repeats (sorted by length):\n";
    fout << string(60, '-') << "\n";
    fout << left
         << setw(6)  << "Rank"
         << setw(10) << "Length"
         << setw(14) << "Occurrences"
         << "Positions (first 6)\n";
    fout << string(60, '-') << "\n";

    for (int i = 0; i < limit; ++i) {
        const auto& r = reps[i];
        fout << left << setw(6) << (i + 1)
             << setw(10) << r.span
             << setw(14) << r.count;

        int show = min((int)r.locs.size(), 6);
        fout << "[ ";
        for (int j = 0; j < show; ++j) {
            fout << r.locs[j];
            if (j + 1 < show) fout << ", ";
        }
        if ((int)r.locs.size() > 6) fout << " ...";
        fout << " ]\n";

        fout << "  Pattern: " << r.motif.substr(0, 60);
        if (r.span > 60) fout << "...";
        fout << "\n\n";
    }
}

/* =========================================================
   PIPELINE ENTRY POINT — 7 stages
   ========================================================= */
int main(int argc, char* argv[]) {
    if (argc < 4) {
        cerr << "Usage: assembler <input.fastq> <k> <output_dir>\n";
        return 1;
    }

    string input_file = argv[1];
    int    kmer_len   = stoi(argv[2]);
    string out_path   = argv[3];

    if (kmer_len < 3 || kmer_len > 63) {
        cerr << "k must be in [3,63]\n"; return 1;
    }
    filesystem::create_directories(out_path);

    Stopwatch total_clock; total_clock.reset();

    /* Stage 1 — Load reads */
    cerr << "[1/7] Reading FASTQ...\n";
    long long num_reads = 0;
    auto read_seqs = load_fastq(input_file, num_reads);
    if (read_seqs.empty()) { cerr << "No reads.\n"; return 1; }
    cerr << "      " << num_reads << " reads loaded.\n";

    /* Stage 2 — Bloom filter + graph construction */
    cerr << "[2/7] Hashing k-mers and building De Bruijn graph (k="
         << kmer_len << ")...\n";

    Stopwatch bloom_clock; bloom_clock.reset();
    ProbSet seen_once(3), seen_twice(3);
    KmerHasher hasher(kmer_len);
    long long kmer_total = 0;

    for (auto& rd : read_seqs) {
        if ((int)rd.size() < kmer_len) continue;
        hasher.initialize(rd, 0);
        uint64_t hv = hasher.get();
        if (seen_once.contains(hv)) seen_twice.add(hv);
        else seen_once.add(hv);
        ++kmer_total;
        for (int i = 1; i + kmer_len <= (int)rd.size(); ++i) {
            hasher.advance(rd[i - 1], rd[i + kmer_len - 1]);
            hv = hasher.get();
            if (seen_once.contains(hv)) seen_twice.add(hv);
            else seen_once.add(hv);
            ++kmer_total;
        }
    }
    double t_bloom = bloom_clock.elapsed_ms();

    Stopwatch graph_clock; graph_clock.reset();
    DBGraph dg;
    for (auto& rd : read_seqs) {
        if ((int)rd.size() < kmer_len) continue;
        hasher.initialize(rd, 0);
        if (seen_twice.contains(hasher.get())) {
            string km  = rd.substr(0, kmer_len);
            string can = min(km, reverse_complement(km));
            dg.insert_edge(can.substr(0, kmer_len - 1), can.substr(1, kmer_len - 1));
        }
        for (int i = 1; i + kmer_len <= (int)rd.size(); ++i) {
            hasher.advance(rd[i - 1], rd[i + kmer_len - 1]);
            if (seen_twice.contains(hasher.get())) {
                string km  = rd.substr(i, kmer_len);
                string can = min(km, reverse_complement(km));
                dg.insert_edge(can.substr(0, kmer_len - 1), can.substr(1, kmer_len - 1));
            }
        }
    }
    double t_graph = graph_clock.elapsed_ms();
    cerr << "      " << dg.node_count() << " nodes, " << dg.edge_count() << " edges.\n";

    /* Stage 3 — Dijkstra assembly */
    cerr << "[3/7] Dijkstra coverage-weighted assembly...\n";
    Stopwatch dijk_clock; dijk_clock.reset();
    string dijk_result = coverage_path_assemble(dg);
    double t_dijk = dijk_clock.elapsed_ms();
    cerr << "      Dijkstra path  : " << dijk_result.size() << " bp.\n";

    /* Stage 4 — Eulerian traversal */
    cerr << "[4/7] Hierholzer Eulerian traversal...\n";
    Stopwatch euler_clock; euler_clock.reset();
    auto euler_nodes = find_euler_path(dg);
    string euler_result;
    if (euler_nodes.size() > 1) {
        euler_result = euler_nodes[0];
        for (size_t i = 1; i < euler_nodes.size(); ++i)
            euler_result += euler_nodes[i].back();
    }
    double t_euler = euler_clock.elapsed_ms();
    cerr << "      Hierholzer path: " << euler_result.size() << " bp.\n";

    string final_seq;
    string strategy;
    if (euler_result.size() >= dijk_result.size() && !euler_result.empty()) {
        final_seq = euler_result; strategy = "Hierholzer (Eulerian)";
    } else if (!dijk_result.empty()) {
        final_seq = dijk_result; strategy = "Dijkstra (coverage-weighted)";
    } else {
        cerr << "      Both failed — falling back to greedy.\n";
        final_seq = greedy_path_assemble(dg); strategy = "Greedy (frequency-weighted)";
    }
    cerr << "      Selected       : " << strategy << " → " << final_seq.size() << " bp.\n";

    /* Stage 5 — Error smoothing */
    cerr << "[5/7] DP error correction...\n";
    Stopwatch dp_clock; dp_clock.reset();
    final_seq = smooth_sequence(final_seq);
    double t_dp = dp_clock.elapsed_ms();

    /* Stage 6 — Suffix array + repeats */
    cerr << "[6/7] Building Suffix Array and LCP Array...\n";
    Stopwatch sa_clock; sa_clock.reset();

    const int REP_MIN = max(kmer_len, 15);
    vector<int>       sa_vec, lcp_vec;
    vector<RepeatEntry> repeat_list;

    if (!final_seq.empty()) {
        string sa_in = final_seq + "$";
        sa_vec      = suffix_array(sa_in);
        lcp_vec     = lcp_array(sa_in, sa_vec);
        repeat_list = detect_repeats(sa_in, sa_vec, lcp_vec, REP_MIN);
    }
    double t_sa = sa_clock.elapsed_ms();
    cerr << "      SA + LCP built. "
         << repeat_list.size() << " repeat region(s) found"
         << " (min_len=" << REP_MIN << ").\n";

    double gc_pct    = compute_gc(final_seq);
    long long n50_bp = compute_n50(final_seq);
    double t_total   = total_clock.elapsed_ms();

    /* Stage 7 — Write output files */
    cerr << "[7/7] Writing outputs...\n";

    {
        ofstream fout(out_path + "/genome.fasta");
        fout << ">GenomeSmith_assembled_sequence method=" << strategy << "\n";
        for (size_t i = 0; i < final_seq.size(); i += 60)
            fout << final_seq.substr(i, 60) << "\n";
    }

    {
        ofstream fout(out_path + "/stats.txt");
        fout << "=== GenomeSmith Assembly Statistics ===\n\n"
             << "Input\n"
             << "  Reads processed   : " << num_reads  << "\n"
             << "  Total k-mers      : " << kmer_total << "\n"
             << "  k-mer size (k)    : " << kmer_len   << "\n\n"
             << "Graph\n"
             << "  Nodes (V)         : " << dg.node_count() << "\n"
             << "  Edges (E)         : " << dg.edge_count() << "\n\n"
             << "Assembly\n"
             << "  Method selected   : " << strategy              << "\n"
             << "  Dijkstra length   : " << dijk_result.size()   << " bp\n"
             << "  Hierholzer length : " << euler_result.size()  << " bp\n"
             << "  Final length      : " << final_seq.size()     << " bp\n"
             << "  GC content        : " << fixed << setprecision(2)
                                         << gc_pct  << " %\n"
             << "  N50               : " << n50_bp  << " bp\n\n"
             << "Repeat Analysis (Suffix Array + LCP)\n"
             << "  Min repeat length : " << REP_MIN             << " bp\n"
             << "  Repeat regions    : " << repeat_list.size()  << "\n";
        if (!repeat_list.empty()) {
            fout << "  Longest repeat    : " << repeat_list[0].span
                 << " bp (" << repeat_list[0].count << "x)\n";
        }
        fout << "\nTime Complexity (Theoretical)\n"
             << "  Rolling Hash      : O(N)           one slide per character\n"
             << "  Bloom Filter      : O(N)           constant insert/query\n"
             << "  Graph Build       : O(V + E)       adjacency list\n"
             << "  Dijkstra          : O((V+E) log V) min-heap relaxation\n"
             << "  Hierholzer        : O(E)            each edge visited once\n"
             << "  DP Correction     : O(N)           single pass\n"
             << "  Suffix Array      : O(n log² n)    prefix doubling\n"
             << "  LCP Array         : O(n)           Kasai's algorithm\n"
             << "  Repeat Finding    : O(n)           LCP scan\n"
             << "  Overall           : O(N + (V+E) log V + n log² n)\n\n"
             << "Execution Time (Measured)\n"
             << "  Total             : " << t_total << " ms\n"
             << "  Hashing           : " << t_bloom << " ms\n"
             << "  Graph Build       : " << t_graph << " ms\n"
             << "  Dijkstra          : " << t_dijk  << " ms\n"
             << "  Hierholzer        : " << t_euler << " ms\n"
             << "  DP Correction     : " << t_dp    << " ms\n"
             << "  Suffix Array+LCP  : " << t_sa    << " ms\n";
    }

    export_graph_json(out_path + "/graph_data.json", dg);
    write_repeat_file(out_path + "/repeats.txt", repeat_list, final_seq, REP_MIN);

    cerr << "Done in " << t_total << " ms.\n";
    cerr << "Outputs: genome.fasta  stats.txt  graph_data.json  repeats.txt\n";
    return 0;
}
