# nullstate Run Report

Run ID: `20260702-182015`

IaC input: `examples\aws-public-s3`

## Verdict

Exploit blocked after remediation

## Findings

- `HIGH` `AWS_S3_PUBLIC_ACCESS_BLOCK_DISABLED` on `aws_s3_bucket_public_access_block.public_logs`: S3 public access block controls are disabled. Evidence: Disabled controls: block_public_acls, block_public_policy, ignore_public_acls, restrict_public_buckets Remediation: Set every aws_s3_bucket_public_access_block control to true.

## Red Team Before Remediation

- Status: `success`
- Evidence: Anonymous S3 read hypothesis succeeded because public access block controls were disabled. Allowlisted tool command returned 0: `python attack.py --target-url offline://aws-public-s3 --stage before --manifest <redacted-local-path>` target=offline://aws-public-s3.

## Blue Team Remediation

Red: offline-mock. Blue: offline-mock. Offline blue team recommended enabling all S3 public access block controls.

```diff
--- a/main.tf
+++ b/main.tf
@@ -27,34 +27,10 @@
 
 resource "aws_s3_bucket_public_access_block" "public_logs" {
   bucket                  = aws_s3_bucket.public_logs.id
-  block_public_acls       = false
-  block_public_policy     = false
-  ignore_public_acls      = false
-  restrict_public_buckets = false
+  block_public_acls       = true
+  block_public_policy     = true
+  ignore_public_acls      = true
+  restrict_public_buckets = true
 }
 
-resource "aws_s3_object" "evidence" {
-  bucket       = aws_s3_bucket.public_logs.id
-  key          = "evidence.txt"
-  content      = "nullstate public S3 evidence"
-  content_type = "text/plain"
-}
 
-resource "aws_s3_bucket_policy" "public_read" {
-  bucket = aws_s3_bucket.public_logs.id
-
-  policy = jsonencode({
-    Version = "2012-10-17"
-    Statement = [
-      {
-        Sid       = "NullstatePublicReadEvidence"
-        Effect    = "Allow"
-        Principal = "*"
-        Action    = "s3:GetObject"
-        Resource  = "${aws_s3_bucket.public_logs.arn}/evidence.txt"
-      }
-    ]
-  })
-
-  depends_on = [aws_s3_bucket_public_access_block.public_logs]
-}
```

## Red Team After Remediation

- Status: `blocked`
- Evidence: Attack path denied after deterministic remediation. Allowlisted tool command returned 0: `python attack.py --target-url offline://aws-public-s3 --stage after --manifest <redacted-local-path>` target=offline://aws-public-s3.

## Runtime Command Evidence

### Before remediation

- Command: `<redacted-local-path> <redacted-local-path> --target-url offline://aws-public-s3 --stage before --manifest <redacted-local-path>`
- Return code: `0`
- Target: `offline://aws-public-s3`
- Classification: `offline deterministic simulation`
- Stdout excerpt:

```text
Attempting anonymous S3 object read against LocalStack AWS endpoint
stage=before target=offline://aws-public-s3
offline target selected; no network request performed
```

### After remediation

- Command: `<redacted-local-path> <redacted-local-path> --target-url offline://aws-public-s3 --stage after --manifest <redacted-local-path>`
- Return code: `0`
- Target: `offline://aws-public-s3`
- Classification: `offline deterministic simulation`
- Stdout excerpt:

```text
Attempting anonymous S3 object read against LocalStack AWS endpoint
stage=after target=offline://aws-public-s3
offline target selected; no network request performed
```


## Remediation Metadata

- Ruleset version: `2026.06.1`
- Scenario: `aws-public-s3`
- Changed: `True`

Rules applied:

- `AWS_S3_BLOCK_PUBLIC_ACCESS`
- `AWS_S3_REMOVE_PUBLIC_READ_POLICY`
- `AWS_S3_REMOVE_PUBLIC_EVIDENCE_OBJECT`

Changed files:

- `main.tf`


## Case Study Notes

nullstate used deterministic IaC analysis for reliability, then layered red-team and blue-team agents over the evidence trail so the demo remains reproducible under hackathon time pressure.
