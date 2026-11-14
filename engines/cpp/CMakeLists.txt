cmake_minimum_required(VERSION 3.16)
project(chess_engine LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(chess_engine
    src/uci.cpp
    src/engine.cpp
    src/search.cpp
    src/evaluate.cpp
    src/logging.cpp
    src/transposition.cpp
    src/move_ordering.cpp
)

target_include_directories(chess_engine PRIVATE
    src
    ${CMAKE_CURRENT_SOURCE_DIR}/chess-library/include
)

target_compile_options(chess_engine PRIVATE
    $<$<OR:$<CONFIG:Release>,$<CONFIG:RelWithDebInfo>>:-march=native>)
target_link_options(chess_engine PRIVATE
    $<$<OR:$<CONFIG:Release>,$<CONFIG:RelWithDebInfo>>:-march=native>)

include(CheckIPOSupported)
check_ipo_supported(RESULT ipo_supported OUTPUT ipo_error)
if(NOT ipo_supported)
    message(FATAL_ERROR "IPO/LTO is not supported: ${ipo_error}")
endif()
set_property(TARGET chess_engine PROPERTY INTERPROCEDURAL_OPTIMIZATION_RELEASE TRUE)
