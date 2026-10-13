cmake_minimum_required(VERSION 3.16)
project(chess_engine LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(chess_engine
    src/uci.cpp
    src/engine.cpp
    src/search.cpp
    src/evaluate.cpp
)

target_include_directories(chess_engine PRIVATE
    src
    ${CMAKE_CURRENT_SOURCE_DIR}/chess-library/include
)
