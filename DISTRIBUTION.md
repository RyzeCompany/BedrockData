# Publishing BedrockData for RyzeMP

Composer package: `ryzemcbe/bedrock-data` (library). Source: https://github.com/RyzeCompany/BedrockData.

Versioned Bedrock network data consumed by RyzeMP; existing asset paths and formats are preserved.

## Public package release checklist

1. Verify the exact revision against the matching RyzeMP core and the other Bedrock dependency.
2. Make this repository public after reviewing its contents and license; a private repository cannot be submitted to public Packagist.org as an installable source package.
3. Create a tested SemVer prerelease tag on `main`, for example `v1.0.0-beta.3` **only if** that version has actually been tested and designated.
4. Submit this repository URL on https://packagist.org/packages/submit and enable its GitHub update hook.
5. Confirm the tagged version resolves and can be downloaded via Composer without special repository configuration.

Once the corresponding release is available on Packagist, developers can install it with:

```bash
composer require ryzemcbe/bedrock-data:<released-version>
```

Do not publish or recommend `dev-main` as a stable API contract. Tags, package registration, and an end-to-end RyzeMP CI build are required for release readiness.
