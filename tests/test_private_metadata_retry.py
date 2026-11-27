import io
import unittest
import urllib.error
from unittest.mock import patch, MagicMock
from engineering_lab import private_metadata as m

PATH="/repos/Jugadru/APEX-Engineering-Lab/commits/"+"a"*40

class MetadataRetryTests(unittest.TestCase):
    def run_with(self,results):
        with patch.dict(m.os.environ,{"APEX_GITHUB_READ_TOKEN":"test-only-secret"}), patch.object(m.urllib.request,"build_opener") as make, patch.object(m.time,"sleep") as wait:
            open_call=make.return_value.open
            open_call.side_effect=results
            try:
                return m.managed_get(PATH),open_call.call_count,wait.call_count
            except ValueError as e:
                return str(e),open_call.call_count,wait.call_count
    def response(self,body=b'{"sha":"synthetic"}'):
        r=MagicMock()
        r.__enter__.return_value.read.return_value=body
        return r
    def http(self,code):
        return urllib.error.HTTPError("https://api.github.com"+PATH,code,"secret-body",{},io.BytesIO(b"secret-body"))
    def test_transient_transport_recovers(self):
        out,calls,waits=self.run_with([OSError("secret"),self.http(503),self.response()])
        self.assertEqual(out,{"sha":"synthetic"})
        self.assertEqual((calls,waits),(3,2))
    def test_permanent_failure_no_retry_and_no_secret(self):
        for code in (301,401,403,404):
            out,calls,waits=self.run_with([self.http(code)])
            self.assertIn("HTTP "+str(code),out)
            self.assertNotIn("secret",out)
            self.assertEqual((calls,waits),(1,0))
    def test_exhausted_transport_remains_blocked(self):
        out,calls,waits=self.run_with([OSError("secret")]*3)
        self.assertIn("failed (transport",out)
        self.assertNotIn("secret",out)
        self.assertEqual((calls,waits),(3,2))
    def test_invalid_json_not_retried(self):
        out,calls,waits=self.run_with([self.response(b'{bad')])
        self.assertIsInstance(out,str)
        self.assertEqual((calls,waits),(1,0))
    def test_oversized_response_not_retried(self):
        out,calls,waits=self.run_with([self.response(b"x"*(m.MAX_API+1))])
        self.assertIn("too large",out)
        self.assertEqual((calls,waits),(1,0))

if __name__=="__main__":unittest.main()
