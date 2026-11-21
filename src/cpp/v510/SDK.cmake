cmake_minimum_required(VERSION 3.20)
project(CrackV510Integration LANGUAGES CXX)
add_executable(CrackV510Example example/example.cpp)
target_compile_features(CrackV510Example PRIVATE cxx_std_17)
target_compile_options(CrackV510Example PRIVATE /utf-8)
target_include_directories(CrackV510Example PRIVATE include)
target_link_libraries(CrackV510Example PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/lib/CrackV510.lib"
  "${CMAKE_CURRENT_SOURCE_DIR}/lib/opencv_world440.lib")
foreach(runtime CrackV510.dll opencv_world440.dll)
  add_custom_command(TARGET CrackV510Example POST_BUILD COMMAND ${CMAKE_COMMAND} -E copy_if_different
    "${CMAKE_CURRENT_SOURCE_DIR}/bin/${runtime}" "$<TARGET_FILE_DIR:CrackV510Example>")
endforeach()
