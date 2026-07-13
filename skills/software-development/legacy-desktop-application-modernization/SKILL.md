---
name: legacy-desktop-application-modernization
description: Modernize incomplete or hardware-bound legacy desktop applications into safe, demonstrable offline runtimes while preserving a path to real-device integration.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, wsl]
metadata:
  hermes:
    tags: [legacy-desktop, winforms, offline-simulation, hardware-abstraction, verification]
    created_by: agent
---

# Legacy Desktop Application Modernization

Use this skill when inheriting a desktop application that compiles or launches but has incomplete business logic, hard-coded database paths, broken login/session behavior, or unavailable production hardware such as PLCs, scanners, cameras, Modbus instruments, or MES endpoints.

## Goal

Produce a safe offline demonstration runtime backed by real project data, without pretending that unverified hardware integration is production-ready. Preserve clean seams for later real-device adapters.

## Workflow

1. **Establish a baseline**
   - Put the imported source under Git before broad edits.
   - Record the actual build command, target framework, architecture, startup form, database files, and tracked generated artifacts.
   - Build on the native Windows toolchain when the project targets WinForms/WPF and orchestration runs from WSL.

2. **Separate data, orchestration, and devices**
   - Introduce repository classes for database reads.
   - Model products/parts, ordered test steps, and step results explicitly.
   - Put sequence execution in an engine that depends on a small device interface rather than directly on controls or vendor SDKs.
   - Keep UI updates in progress callbacks and marshal them safely to the UI thread.

3. **Implement safe offline adapters**
   - Map known step methods (PLC I/O, scan, delay, vision, Modbus, string checks, screen changes) to deterministic or bounded simulations.
   - Generate visibly synthetic identifiers such as `SIM...` barcodes.
   - Never execute database-provided scripts in offline mode; log an explicit simulated pass instead.
   - Handle unknown methods with an explicit safe simulation result and visible logging, not silent omission.

4. **Drive the demo from production-like data**
   - Load product/part choices and ordered process steps from the shipped database.
   - Parameterize queries and account for null/blank override values.
   - Resolve runtime assets from `AppContext.BaseDirectory`, then configure project copy rules for databases and settings.

5. **Repair application lifecycle**
   - Make login return a dialog result; create the main form once after successful authentication.
   - Verify both password and access level from the database using parameterized queries.
   - Keep session state centralized and refresh menu/feature permissions after login changes.
   - Reuse or activate settings windows rather than opening duplicates.

6. **Make safety mode explicit**
   - Require an `OfflineSimulation` configuration flag.
   - Fail closed when the flag is missing, malformed, or false unless a separately reviewed real-device runtime exists.
   - Label the UI and logs so operators cannot confuse simulation with production.

7. **Cancellation and shutdown**
   - Give each run a cancellation token source.
   - Disable conflicting controls while running and restore them in `finally`.
   - Cancel on Stop and form close; avoid logging “complete” after cancellation or disposal.

8. **Verify the deliverable**
   - Run a clean native Windows build and report exact warning/error counts.
   - Launch the built executable and verify the expected initial window is responsive.
   - Exercise login and at least one full simulated sequence when desktop automation is available.
   - Review `git diff --check`, remove temporary build trees, and distinguish source changes from generated `bin/obj` churn.
   - Commit only after fresh verification.

## WSL / Windows execution pattern

Use Windows PowerShell for native builds and launches:

```bash
powershell.exe -NoProfile -Command "Set-Location 'C:\\path\\to\\repo'; dotnet build .\\App\\App.csproj -c Debug"
```

A launched executable may lock tracked output files. Stop the process before restoring legacy tracked `bin/` or `obj/` artifacts.

## Pitfalls

- **Build success is not runtime verification:** launch the generated executable and confirm its main window is responsive.
- **Generated artifacts are tracked:** legacy repositories may track `bin/obj`; builds create noisy diffs. Verify first, stop launched processes, then restore generated files before committing source.
- **Temporary intermediate output inside the project:** SDK-style projects recursively glob source. A nested alternate `obj` directory can cause duplicate assembly attributes. Put temporary outputs outside the project tree or explicitly exclude them.
- **Relative database paths:** they depend on process working directory and commonly break after publishing or launching from shortcuts.
- **Fake real-device mode:** do not expose a “real” toggle until device models, register maps, message framing, timeouts, and safety behavior are known.
- **Unsafe script replay:** database script fields are data from an unknown trust boundary; never run them merely to make a demo pass.
- **Password-only success checks:** count queries that ignore password predicates can authenticate invalid credentials. Verify the selected user and password together and load the matching level.

## Supporting material

- `references/winforms-offline-runtime-case.md` — concise case notes for Access-driven WinForms simulation and native Windows verification from WSL.
