#include "logging.hpp"

#include <charconv>
#include <cerrno>
#include <cstdint>
#include <cstdlib>
#include <ctime>
#include <exception>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string_view>
#include <system_error>
#include <utility>

#if defined(_WIN32)
#include <process.h>
#else
#include <unistd.h>
#endif

namespace logging {
namespace {

std::string local_timestamp() {
    const std::time_t now = std::time(nullptr);
    if (now == static_cast<std::time_t>(-1)) {
        return "-";
    }
    std::tm local{};
#if defined(_WIN32)
    if (localtime_s(&local, &now) != 0) {
        return "-";
    }
#else
    if (localtime_r(&now, &local) == nullptr) {
        return "-";
    }
#endif
    char formatted[32];
    if (std::strftime(formatted, sizeof formatted, "%Y-%m-%d %H:%M:%S", &local) == 0) {
        return "-";
    }
    return formatted;
}

long current_process_id() {
#if defined(_WIN32)
    return static_cast<long>(_getpid());
#else
    return static_cast<long>(::getpid());
#endif
}

std::string errno_message() {
    return std::generic_category().message(errno);
}

std::string sanitized_for_warning(std::string_view value) {
    constexpr std::size_t max_characters = 80;
    std::string sanitized;
    sanitized.reserve(max_characters + 3);
    for (const char character : value) {
        if (sanitized.size() == max_characters) {
            sanitized.append("...");
            break;
        }
        const auto byte = static_cast<unsigned char>(character);
        const bool is_control = byte < 0x20 || byte == 0x7f;
        sanitized.push_back(is_control || character == '"' ? '?' : character);
    }
    return sanitized;
}

int env_int(const char* name, int fallback, int minimum) {
    const char* raw = std::getenv(name);
    if (raw == nullptr || raw[0] == '\0') {
        return fallback;
    }
    const std::string_view text(raw);
    int value = 0;
    const std::from_chars_result parsed = std::from_chars(text.data(), text.data() + text.size(), value);
    if (parsed.ec != std::errc() || parsed.ptr != text.data() + text.size() || value < minimum) {
        return fallback;
    }
    return value;
}

bool env_is(const char* name, std::string_view expected) {
    const char* value = std::getenv(name);
    return value != nullptr && expected == value;
}

std::uint64_t nodes_per_second(std::uint64_t nodes, std::int64_t elapsed_ms) {
    if (elapsed_ms <= 0) {
        return 0;
    }
    const auto ms = static_cast<std::uint64_t>(elapsed_ms);
    return (nodes / ms) * 1000 + (nodes % ms) * 1000 / ms;
}

std::string one_decimal(double value) {
    std::ostringstream formatted;
    formatted << std::fixed << std::setprecision(1) << value;
    return formatted.str();
}

enum class LogMode {
    Off,
    Summary,
    Trace,
};

LogMode log_mode() {
    const char* configured = std::getenv("CHESS_LOG");
    if (configured == nullptr || configured[0] == '\0') {
        return LogMode::Trace;
    }
    const std::string_view value(configured);
    if (value == "trace") {
        return LogMode::Trace;
    }
    if (value == "summary") {
        return LogMode::Summary;
    }
    if (value == "off" || value == "0") {
        return LogMode::Off;
    }
    std::cerr << "unknown CHESS_LOG value \"" << sanitized_for_warning(value) << "\"; using trace\n";
    return LogMode::Trace;
}

template <typename Action>
void try_logging(Action&& action) {
    try {
        std::forward<Action>(action)();
    } catch (const std::exception& ex) {
        std::cerr << "logging failed: " << ex.what() << '\n';
    } catch (...) {
        std::cerr << "logging failed\n";
    }
}

class Logger {
public:
    static Logger& instance();

    Logger(const Logger&) = delete;
    Logger& operator=(const Logger&) = delete;

    void begin_game();
    void log_search(SearchStats stats);
    void flush();
    bool should_include_fen() const { return include_fen_; }

private:
    Logger();
    ~Logger();

    void open_trace();
    void record(const SearchStats& stats);
    void write_trace(const SearchStats& stats);
    void write_summary();
    void report_summary_failure(const char* action);
    void disable(const char* reason);

    bool enabled_ = false;
    bool include_fen_ = false;
    bool trace_ok_ = false;
    bool summary_error_reported_ = false;
    int every_ = 1;
    int min_elapsed_ms_ = 0;
    int game_number_ = 0;
    int move_number_ = 0;
    std::uint64_t searches_seen_ = 0;
    std::string engine_name_;
    std::uint64_t search_count_ = 0;
    std::uint64_t total_nodes_ = 0;
    std::int64_t total_elapsed_ms_ = 0;
    std::int64_t max_elapsed_ms_ = 0;
    std::uint64_t max_nodes_ = 0;
    std::uint64_t full_budget_count_ = 0;
    long process_id_ = 0;
    std::string started_;
    std::filesystem::path summary_path_;
    std::filesystem::path trace_path_;
    std::ofstream trace_;
};

Logger& Logger::instance() {
    static Logger logger;
    return logger;
}

Logger::Logger() {
    try {
        const LogMode mode = log_mode();
        if (mode == LogMode::Off) {
            return;
        }

        const char* configured_directory = std::getenv("CHESS_LOG_DIR");
        const std::filesystem::path log_directory =
            configured_directory != nullptr && configured_directory[0] != '\0' ? configured_directory : "logs";
        std::error_code create_error;
        std::filesystem::create_directories(log_directory, create_error);
        if (create_error) {
            std::cerr << "could not create " << log_directory.string() << ": " << create_error.message() << '\n';
            return;
        }

        process_id_ = current_process_id();
        started_ = local_timestamp();
        summary_path_ = log_directory / ("summary-" + std::to_string(process_id_) + ".txt");

        if (mode == LogMode::Trace) {
            every_ = env_int("CHESS_LOG_EVERY", 1, 1);
            min_elapsed_ms_ = env_int("CHESS_LOG_MIN_MS", 0, 0);
            trace_path_ = log_directory / ("search-" + std::to_string(process_id_) + ".tsv");
            open_trace();
            if (trace_ok_) {
                include_fen_ = env_is("CHESS_LOG_VERBOSE", "1");
            }
        }

        enabled_ = true;
    } catch (const std::exception& ex) {
        disable(ex.what());
    } catch (...) {
        disable(nullptr);
    }
}

Logger::~Logger() {
    try {
        flush();
    } catch (...) {
    }
}

void Logger::open_trace() {
    constexpr std::string_view header =
        "engine\tgame\tmove_number\tside\tdepth\tnodes\tnps\telapsed_ms\tbudget_ms\tfull_budget\tscore\tmove\tfen\n";
    trace_.open(trace_path_, std::ios::out | std::ios::binary | std::ios::trunc);
    if (!trace_) {
        std::cerr << "could not open " << trace_path_.string() << ": " << errno_message() << '\n';
        return;
    }
    trace_.write(header.data(), static_cast<std::streamsize>(header.size()));
    trace_.flush();
    if (!trace_) {
        const std::string message = errno_message();
        trace_.close();
        std::error_code remove_error;
        std::filesystem::remove(trace_path_, remove_error);
        std::cerr << "could not write " << trace_path_.string() << ": " << message << '\n';
        return;
    }
    trace_ok_ = true;
}

void Logger::disable(const char* reason) {
    if (reason == nullptr) {
        std::cerr << "logging disabled\n";
    } else {
        std::cerr << "logging disabled: " << reason << '\n';
    }
    enabled_ = false;
    include_fen_ = false;
    trace_ok_ = false;
    if (trace_.is_open()) {
        trace_.close();
    }
}

void Logger::begin_game() {
    if (!enabled_) {
        return;
    }
    try_logging([this] {
        ++game_number_;
        move_number_ = 0;
        write_summary();
    });
}

void Logger::log_search(SearchStats stats) {
    if (!enabled_) {
        return;
    }
    try_logging([this, &stats] {
        // The first search starts game 1 when ucinewgame was not sent.
        if (game_number_ == 0) {
            ++game_number_;
            move_number_ = 0;
        }
        ++move_number_;
        stats.game = game_number_;
        stats.move_number = move_number_;
        record(stats);
        write_trace(stats);
        write_summary();
    });
}

void Logger::flush() {
    if (!enabled_) {
        return;
    }
    try_logging([this] { write_summary(); });
}

void Logger::record(const SearchStats& stats) {
    if (engine_name_.empty()) {
        engine_name_ = stats.engine;
    }
    ++search_count_;
    total_nodes_ += stats.nodes;
    total_elapsed_ms_ += stats.elapsed_ms;
    if (stats.elapsed_ms > max_elapsed_ms_) {
        max_elapsed_ms_ = stats.elapsed_ms;
    }
    if (stats.nodes > max_nodes_) {
        max_nodes_ = stats.nodes;
    }
    if (stats.full_budget) {
        ++full_budget_count_;
    }
}

void Logger::write_trace(const SearchStats& stats) {
    if (!trace_ok_) {
        return;
    }
    ++searches_seen_;
    if (every_ > 1 && searches_seen_ % static_cast<std::uint64_t>(every_) != 0) {
        return;
    }
    if (stats.elapsed_ms < min_elapsed_ms_) {
        return;
    }

    std::ostringstream row;
    row << stats.engine << '\t' << stats.game << '\t' << stats.move_number << '\t' << stats.side << '\t'
        << stats.depth << '\t' << stats.nodes << '\t' << nodes_per_second(stats.nodes, stats.elapsed_ms) << '\t'
        << stats.elapsed_ms << '\t' << stats.budget_ms << '\t' << (stats.full_budget ? 1 : 0) << '\t';
    if (stats.score.has_value()) {
        row << *stats.score;
    }
    row << '\t' << stats.move << '\t' << stats.fen << '\n';

    trace_ << row.str();
    trace_.flush();
    if (!trace_) {
        const std::string message = errno_message();
        trace_ok_ = false;
        trace_.close();
        std::cerr << "could not write " << trace_path_.string() << ": " << message << '\n';
    }
}

void Logger::write_summary() {
    const double searches = static_cast<double>(search_count_);
    std::ostringstream summary;
    summary << "engine: " << (engine_name_.empty() ? "-" : engine_name_) << '\n'
            << "pid: " << process_id_ << '\n'
            << "started: " << started_ << '\n'
            << "games: " << game_number_ << '\n'
            << "searches: " << search_count_ << '\n'
            << "total_nodes: " << total_nodes_ << '\n'
            << "total_elapsed_ms: " << total_elapsed_ms_ << '\n'
            << "nps: " << nodes_per_second(total_nodes_, total_elapsed_ms_) << '\n'
            << "mean_elapsed_ms: "
            << one_decimal(search_count_ == 0 ? 0.0 : static_cast<double>(total_elapsed_ms_) / searches) << '\n'
            << "mean_nodes: "
            << one_decimal(search_count_ == 0 ? 0.0 : static_cast<double>(total_nodes_) / searches) << '\n'
            << "max_elapsed_ms: " << max_elapsed_ms_ << '\n'
            << "max_nodes: " << max_nodes_ << '\n'
            << "full_budget: " << full_budget_count_ << '\n';

    std::ofstream out(summary_path_, std::ios::out | std::ios::binary | std::ios::trunc);
    if (!out) {
        report_summary_failure("open");
        return;
    }
    out << summary.str();
    out.flush();
    if (!out) {
        report_summary_failure("write");
    }
}

void Logger::report_summary_failure(const char* action) {
    if (summary_error_reported_) {
        return;
    }
    summary_error_reported_ = true;
    std::cerr << "could not " << action << ' ' << summary_path_.string() << ": " << errno_message() << '\n';
}

}

void begin_game() {
    Logger::instance().begin_game();
}

void log_search(SearchStats stats) {
    Logger::instance().log_search(std::move(stats));
}

void flush() {
    Logger::instance().flush();
}

bool should_include_fen() {
    return Logger::instance().should_include_fen();
}

}
