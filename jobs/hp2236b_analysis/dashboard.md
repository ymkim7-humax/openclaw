# HP2236B Analysis Dashboard

- **Last Continuity Check:** 2026-03-15 05:52 PM (Asia/Seoul)
- **Active Sub-agents:** 1 (`agent:main:subagent:8ee1568d-225c-4d7a-8b53-98028d6dbf3f`)
- **Status:** Continuity check at 05:42 PM found 0 active sub-agents. A new analysis sub-agent was spawned.
- **Workdir Compliance:** Verified.
- **Mandatory Policy:** Strictly restricted to `.openclaw/workspace/`. `/home/ymkim7/work/` is avoided.

## Recent Findings (2026-03-15)
### AI/Llama Search
- No hits for "llama" or "tensor" in the source tree.
- "Inference" hits found in ARM Trusted Firmware (ATF) docs (`porting-guide.rst`) and `ethosn_npu.mk`, likely generic Ethos-N NPU support in the bootloader.
- "Neural" hits found in U-Boot documentation and device tree files for "Edgeble Neural Compute Module" (RK3588/RV1126), suggesting broad SoC support but not necessarily active HP2236B features.

### Neural Engine / NPU
- Found explicit NPU (Neural Processing Unit) support in `release_bsp/NPU/` and `modules/private/NPU/`.
- NPU binaries identified: `npu_rv32.bin` and `npu_data.bin`.
- The NPU in this platform appears to be a RISC-V (rv32) based co-processor used for "WiFi Offload" and "HWNAT" (Hardware Network Address Translation).
- No evidence of LLM/Llama-specific acceleration; "Neural" here likely refers to packet processing acceleration or basic pattern matching rather than generative AI.

### Unusual Apps/Dependencies
- `apps/hni/3rdpartyagent`: Uses `mosquitto` and `jsonschema`. Vendor code (`wa_vendor.cpp`) references "AIS" (likely the ISP name).
- `apps/hni/meshapi`: Communicates with `/services/mesh/putAPInformation/` using hardcoded credentials.
- `apps/hni/aisspeedtest`: A custom speed test implementation.
- `apps/hni/corecpp_lib`: A foundational C++ library for Humax/Airoha apps.

### Conclusion on "AI-assisted code"
- No direct evidence of AI-generated code markers or LLM integration in the user-space applications.
- "Neural" hardware exists but is dedicated to networking/WiFi offload.
