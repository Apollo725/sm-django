from django.test.runner import DiscoverRunner


class ExistingDBTestRunner(DiscoverRunner):

    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        print test_labels
        self.setup_test_environment()
        suite = self.build_suite(test_labels, extra_tests)
        result = self.run_suite(suite)
        self.teardown_test_environment()
        return self.suite_result(suite, result)
