cmake_minimum_required(VERSION 3.14)
project(uefitool_pybind)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Enable debug info
set(CMAKE_BUILD_TYPE Debug)
set(CMAKE_CXX_FLAGS_DEBUG "-g -O0")

# If using pybind11 as submodule:

# Use pybind11 as submodule or system package
#add_subdirectory(pybind11)
find_package(pybind11 REQUIRED)

# Recursively collect all .cpp and .c files under UEFITool/common/
file(GLOB_RECURSE UEFITOOL_SOURCES
    "UEFITool/common/*.cpp"
    "UEFITool/common/*.c"
)

pybind11_add_module(uefitool
    fitparser_bindings.cpp
    fitparser_wrapper.cpp
    ${UEFITOOL_SOURCES}
)

# Include headers
target_include_directories(uefitool PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/UEFITool/common
)

# Enable FIT parsing if required
target_compile_definitions(uefitool PRIVATE
    U_ENABLE_FIT_PARSING_SUPPORT
)

