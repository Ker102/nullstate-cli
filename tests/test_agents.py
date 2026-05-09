import unittest

from nullstate.agents import LlmAgent


class AgentTests(unittest.TestCase):
    def test_offline_agent_response_matches_aws_s3_context(self):
        red = LlmAgent("red", "unused").complete(
            "system",
            "Find an exploit for AWS_S3_PUBLIC_ACCESS_BLOCK_DISABLED",
            offline=True,
        )
        blue = LlmAgent("blue", "unused").complete(
            "system",
            "Diagnose and patch AWS_S3_PUBLIC_ACCESS_BLOCK_DISABLED",
            offline=True,
        )

        self.assertIn("S3", red.content)
        self.assertIn("public access block", blue.content)
        self.assertNotIn("Azure Blob", red.content)


if __name__ == "__main__":
    unittest.main()
