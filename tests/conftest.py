"""Test configuration for pytest"""

import pytest


@pytest.fixture
def sample_html():
    """Sample HTML for testing"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Test Page</title>
        <meta name="description" content="This is a test page">
        <meta name="keywords" content="test, sample, page">
        <meta property="og:title" content="Test OG Title">
        <meta property="og:description" content="Test OG Description">
    </head>
    <body>
        <h1>Main Heading</h1>
        <h2>Subheading One</h2>
        <h2>Subheading Two</h2>
        <p>This is a test paragraph with some content.</p>
        <p>Another paragraph for testing purposes.</p>
        <a href="/internal-link">Internal Link</a>
        <a href="https://external.com">External Link</a>
        <img src="/image.jpg" alt="Test Image">
        <script src="/script.js"></script>
    </body>
    </html>
    """


@pytest.fixture
def sample_url():
    """Sample URL for testing"""
    return "https://example.com/test-page"
