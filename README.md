# ProxyManager Releases

Official release repository for ProxyManager - AI Gateway Proxy Management for macOS.

## 📦 Download

Visit the [latest release](https://github.com/danielraffel/proxymanager-releases/releases/latest) to download ProxyManager.

### System Requirements
- macOS 13.0 (Ventura) or later
- Apple Silicon or Intel Mac

## 🔄 Update Channels

ProxyManager offers three update channels:

- **Release** (Recommended): Stable releases, thoroughly tested
- **Debug**: Bleeding edge builds with debug symbols
- **Prod**: Production builds for critical deployments

## 📖 Documentation

- [Architecture](docs/ARCHITECTURE.md) - System design and components
- [V1 Workflow](docs/V1_WORKFLOW.md) - Manual update process
- [V2 Migration](docs/V2_MIGRATION.md) - Upgrading to Sparkle auto-updates
- [Reuse Guide](docs/REUSE_GUIDE.md) - Adapt this system for your app

## 🛠 For Developers

This repository contains the complete distribution infrastructure for ProxyManager:

- **Sparkle appcast feeds** (`appcast/*.xml`)
- **Release artifacts** (`releases/`)
- **Build automation scripts** (`scripts/`)
- **GitHub Actions workflows** (`.github/workflows/`)

### Building Releases

See the main [ai-gateway repository](https://github.com/danielraffel/ai-gateway) for build instructions.

### Reusing This Template

This distribution system is designed to be reusable. See [REUSE_GUIDE.md](docs/REUSE_GUIDE.md) for instructions on adapting it for your macOS app.

## 📄 License

MIT License - see main repository for details.

## 🔗 Links

- [Main Repository](https://github.com/danielraffel/ai-gateway)
- [Report Issues](https://github.com/danielraffel/ai-gateway/issues)
- [Release Notes](https://github.com/danielraffel/proxymanager-releases/releases)
