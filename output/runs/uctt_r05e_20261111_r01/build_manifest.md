# 构建身份

C++17，MSVC v142 19.29.30159 x64，OpenCV4.4，Release /O2 /fp:precise /utf-8，4 native threads。

- B0.dll: `5b54fe10b0ccf8b6b92c74a44ea299d4a811d02a028ecde759acd2c4816980b4`
- B1.dll: `f13117955214a947b31aa329a7b2afd80c6d3d5f0cb30e56f522acf571a80df4`
- B2.dll: `02f104201b1236f52ec11c42912f93c97ab4d0473ae5754e0c3e8a1948ba3c9f`
- R03Original.exe: `eb86726024a8e7e94a3f90802373afe97af60e9dda713803aab839307ee2e24b`
- EvidenceContracts.exe: `1cca231328c5fdff80cd66f880744b41e5379a97188b35966afcc1048c993f3e`
- opencv_world440.dll: `5424d86f4b63ca0e700672768296ca6374807a9db6b0c88f9bcc0940cd06c8ac`

生产DLL身份、原图/P1P2库存与标注ZIP身份见frozen_manifest_r05e.json；每原图在读入前核对hash。
