# SPDX-License-Identifier: MIT
cmake_minimum_required(VERSION 3.21)

project(still_life_material LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_CXX_VISIBILITY_PRESET hidden)
set(CMAKE_VISIBILITY_INLINES_HIDDEN ON)

find_package(gman CONFIG REQUIRED)

add_library(gilded MODULE shaders/gmangilded.cpp)
target_link_libraries(gilded PRIVATE gman::gman_core)
set_target_properties(gilded PROPERTIES PREFIX "lib" SUFFIX ".so")

enable_testing()

add_executable(gildednormal_test tests/gildednormal_test.cpp)
target_include_directories(gildednormal_test PRIVATE shaders)
target_link_libraries(gildednormal_test PRIVATE gman::gman_core)
add_test(NAME gildednormal COMMAND gildednormal_test)
set_tests_properties(gildednormal PROPERTIES LABELS unit TIMEOUT 60)
