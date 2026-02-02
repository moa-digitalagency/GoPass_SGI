# GO-PASS SGI-GP Documentation

## Système de Gestion Intégrée GO-PASS

### Overview
GO-PASS SGI-GP is an integrated pass management system for issuing, validating, and tracking access passes.

### Features
- User management with role-based access control
- Pass generation with QR codes
- Pass validation interface
- Access logging and audit trail
- Dashboard with statistics

### User Roles
- **Admin**: Full system access
- **Agent**: Can manage passes and users
- **Holder**: Can view their own passes

### Default Credentials
- Admin: `admin` / `admin123`
- Agent: `agent` / `agent123`

### API Endpoints
- `GET /api/passes/search?q=query` - Search passes
- `GET /api/users/search?q=query` - Search users
- `POST /api/validate` - Validate a pass
- `GET /api/statistics` - Get system statistics
