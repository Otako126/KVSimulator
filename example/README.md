# Example programs

## `sample_program.py`

A minimal executable example for this simulator.

### What it shows

- Building the simulator from `simulator.yaml`
- External write into an `IO_IMAGE` device (`R0`)
- Running step scans and observing delayed reflection (`NEXT_SCAN` / scan-boundary apply)
- Reading resulting values from `MR` and `DM`

### Run

```bash
python example/sample_program.py
```

Expected behavior: values update across scan boundaries rather than immediately for deferred consistency devices.
