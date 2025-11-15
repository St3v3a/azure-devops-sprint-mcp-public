# Changelog

All notable changes to the Azure DevOps Sprint MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2024-11-15

### Added
- **Multi-Project Support** - Work with multiple Azure DevOps projects simultaneously
  - ServiceManager for lazy-loaded project services
  - Per-project cache isolation (95%+ hit rate)
  - All 13 tools now accept optional `project` parameter
  - Backward compatible with default project configuration
- **Health & Monitoring Tools**
  - `health_check()` - Server health and authentication status
  - `get_service_statistics()` - Performance metrics and cache statistics
- **Comprehensive Documentation**
  - Complete README.md with user guide + architecture guide
  - Consolidated docs in docs/ folder
  - WSL/Claude Desktop setup guide for Windows users
- **Maintenance Scripts**
  - `scripts/setup.sh` - Automated first-time setup
  - `scripts/start.sh` - Start server (Docker or Python)
  - `scripts/stop.sh` - Stop server
  - `scripts/restart.sh` - Restart server

### Changed
- `AZURE_DEVOPS_PROJECT` environment variable now optional (used as default)
- Reorganized repository structure for cleaner public release
- Documentation consolidated from 15+ files into 7 focused guides

### Fixed
- Service caching now properly isolated per project
- Import errors in ServiceManager validation

## [2.0.0] - 2024-11-01

### Added
- **Security Hardening** (validation.py)
  - Whitelist-based input validation (states, types, fields)
  - WIQL query sanitization (SQL injection prevention)
  - 32KB query limit enforcement
  - Field name validation (60+ allowed fields)
  - Path traversal attack prevention

- **Error Handling** (errors.py, decorators.py)
  - 10 custom exception classes with helpful messages
  - Automatic retry with exponential backoff (1s→2s→4s)
  - Request timeouts (30s default, configurable)
  - Rate limit handling (respects Retry-After header)
  - Transient error recovery (500, 502, 503, 504)

- **Performance Optimization** (constants.py, cache.py)
  - TTL-based caching (5-minute default)
  - Pre-defined field sets (70% smaller responses)
  - Query limits (100 default, 500 sprint, 20,000 max)
  - Batch operations (200 IDs per batch)
  - Automatic cache invalidation on updates

- **Advanced Query Tools**
  - `get_work_item_hierarchy()` - Recursive parent-child relationships
  - `search_work_items()` - Indexed full-text search
  - `get_historical_work_items()` - Historical state queries

- **Authentication Enhancements**
  - Automatic token refresh (5 minutes before expiry)
  - Enhanced error messages with scope requirements
  - Token expiry monitoring

### Changed
- All services now inherit from `CachedService` base class
- All operations use `@azure_devops_operation` decorator
- Field selection optimized (specific fields vs expand='All')
- WIQL queries now use TOP clauses (no unbounded queries)
- Server version bumped to 2.0

### Performance Improvements
- 70% reduction in response sizes (specific field selection)
- Sub-second cached query responses
- 95%+ cache hit rate target achieved
- 100% query limit enforcement

## [1.0.0] - 2024-10-01

### Added
- Initial release of Azure DevOps Sprint MCP Server
- FastMCP-based server with 10 core tools
- Azure authentication (Managed Identity, Service Principal, PAT)
- Sprint and work item management
- Docker deployment support
- Basic caching implementation
- WIQL query support

### Features
- 10 MCP Tools for work item and sprint operations
- 3 MCP Resources (current sprint, sprint details, work item details)
- Multi-method authentication (Managed Identity → Service Principal → PAT)
- Docker and STDIO transport modes
- Basic error handling and logging

---

## Version Numbering

- **Major** (X.0.0) - Breaking changes, major feature additions
- **Minor** (x.X.0) - New features, backward compatible
- **Patch** (x.x.X) - Bug fixes, minor improvements

---

[2.1.0]: https://github.com/yourusername/azure-devops-sprint-mcp/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/yourusername/azure-devops-sprint-mcp/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/yourusername/azure-devops-sprint-mcp/releases/tag/v1.0.0
