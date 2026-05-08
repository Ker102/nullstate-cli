# Cost Report

## Summary

V1 is designed to keep cloud spend near zero by default. Offline mode runs locally. LocalStack runs in Docker on the operator machine. AMD Developer Cloud usage is limited to model-serving evidence collection for the hackathon.

## Cost items

| Item | Expected cost | Notes |
|---|---:|---|
| nullstate CLI | 0 | local Python package |
| Offline demo | 0 | no cloud or model endpoint |
| LocalStack Azure | depends on LocalStack access | requires auth token |
| AMD Developer Cloud | hackathon credits | used for MI300X model endpoint |
| GitHub Actions | low/free tier dependent | tests are lightweight |

## Controls

- No real Azure by default.
- No long-running cloud resources created by the CLI.
- Local sandboxes can be stopped with `nullstate sandbox down`.

## Future tracking

Record actual hackathon model-serving runtime, GPU hours, and any LocalStack or cloud access costs before publishing the case study.
