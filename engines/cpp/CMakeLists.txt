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

# none: transposition-table move only (dumbledore)
# enpassant: MVV-LVA plus an en passant capture check (dumbledore-v1)
# promotion: MVV-LVA plus a promotion check (dumbledore-v2)
# either: MVV-LVA plus both checks (dumbledore-v3)
set(MOVE_ORDER_MODE "none" CACHE STRING "Move ordering variant: none, enpassant, promotion, or either")
set_property(CACHE MOVE_ORDER_MODE PROPERTY STRINGS none enpassant promotion either)

if(MOVE_ORDER_MODE STREQUAL "enpassant")
    target_compile_definitions(chess_engine PRIVATE MOVE_ORDER_MODE=1 "ENGINE_LABEL=\"dumbledore-v1\"")
elseif(MOVE_ORDER_MODE STREQUAL "promotion")
    target_compile_definitions(chess_engine PRIVATE MOVE_ORDER_MODE=2 "ENGINE_LABEL=\"dumbledore-v2\"")
elseif(MOVE_ORDER_MODE STREQUAL "either")
    target_compile_definitions(chess_engine PRIVATE MOVE_ORDER_MODE=3 "ENGINE_LABEL=\"dumbledore-v3\"")
elseif(MOVE_ORDER_MODE STREQUAL "none")
    target_compile_definitions(chess_engine PRIVATE MOVE_ORDER_MODE=0 "ENGINE_LABEL=\"dumbledore\"")
else()
    message(FATAL_ERROR "Unknown MOVE_ORDER_MODE '${MOVE_ORDER_MODE}'")
endif()
