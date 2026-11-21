set(SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/..")
set(GEN_DIR "${CMAKE_CURRENT_BINARY_DIR}")
set(sdk_project "${SOURCE_DIR}/../../GrayDetectionV2")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
    "${SOURCE_DIR}/a/include/CrackV4.h" "${SOURCE_DIR}/a/include/CrackV4.hpp"
    "${SOURCE_DIR}/v512/exports.def" "${sdk_project}/VERSION.txt")
include("${sdk_project}/generate_sdk.cmake")

add_library(GrayDetectionV2 SHARED ../a/CrackV4.cpp geometry.cpp mapping.cpp evidence.cpp tracking.cpp
    ../v510/registration.cpp ../v512/material.cpp "${GEN_DIR}/GrayDetectionV2.def" "${GEN_DIR}/GrayDetectionV2.rc")
add_custom_target(CrackV63 DEPENDS GrayDetectionV2)
target_include_directories(GrayDetectionV2 PRIVATE ../a/include ../a/internal)
target_compile_definitions(GrayDetectionV2 PRIVATE CRACK_V63_BACKEND CRACK_V512_BACKEND CRACK_V4_EXPORTS NOMINMAX)
target_link_libraries(GrayDetectionV2 PRIVATE opencv440)
target_compile_options(GrayDetectionV2 PRIVATE "$<$<COMPILE_LANGUAGE:CXX>:/FI${GEN_DIR}/GrayDetectionV2_build.h;/O2;/fp:precise;/utf-8>")
add_custom_command(TARGET GrayDetectionV2 POST_BUILD COMMAND ${CMAKE_COMMAND} -E copy_if_different
    "${CV440}/bin/opencv_world440.dll" "$<TARGET_FILE_DIR:GrayDetectionV2>")
