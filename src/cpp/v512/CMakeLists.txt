add_library(CrackV512 SHARED ../a/CrackV4.cpp ../v510/geometry.cpp ../v510/registration.cpp evidence.cpp tracking.cpp material.cpp exports.def)
set_target_properties(CrackV512 PROPERTIES OUTPUT_NAME CrackV4)
target_include_directories(CrackV512 PRIVATE ../a/include ../a/internal)
target_compile_definitions(CrackV512 PRIVATE CRACK_V512_BACKEND CRACK_V4_EXPORTS NOMINMAX)
target_link_libraries(CrackV512 PRIVATE opencv440)
target_compile_options(CrackV512 PRIVATE /O2 /fp:precise /utf-8)
add_custom_command(TARGET CrackV512 POST_BUILD COMMAND ${CMAKE_COMMAND} -E copy_if_different
    "${CV440}/bin/opencv_world440.dll" "$<TARGET_FILE_DIR:CrackV512>")
