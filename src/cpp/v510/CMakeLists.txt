add_library(CrackV510 SHARED api.cpp geometry.cpp registration.cpp evidence.cpp tracking.cpp)
target_compile_definitions(CrackV510 PRIVATE CRACK510_BUILD NOMINMAX)
target_compile_options(CrackV510 PRIVATE /O2 /fp:precise /utf-8)
target_include_directories(CrackV510 PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}")
target_link_libraries(CrackV510 PRIVATE opencv440)
add_custom_command(TARGET CrackV510 POST_BUILD COMMAND ${CMAKE_COMMAND} -E copy_if_different
    "${CV440}/bin/opencv_world440.dll" "$<TARGET_FILE_DIR:CrackV510>")

add_executable(CrackV510Example example.cpp)
target_link_libraries(CrackV510Example PRIVATE CrackV510 opencv440)
target_compile_options(CrackV510Example PRIVATE /utf-8)
