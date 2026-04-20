
const fs = require('fs');
const path = require('path');

const mockDir = path.join(__dirname, '../mock_responses');
if (!fs.existsSync(mockDir)) {
  fs.mkdirSync(mockDir, { recursive: true });
}

// 1. Login Result (Handshake)
const loginHandshake = {
  status: 'success',
  data: {
    selection_token: 'handshake_token_v2_xyz',
    user_id: 'u-789',
    is_new: false,
    companies: [
      {
        company_id: 'c1',
        company_name: 'Logistic Tijuana WH',
        role_names: ['Admin', 'Manager'],
        is_new: false,
        group_id: 'g1'
      },
      {
        company_id: 'c2',
        company_name: 'San Diego Hub',
        role_names: ['Operator'],
        is_new: false,
        group_id: 'g1'
      }
    ]
  },
  message: 'Authentication successful. Please select a company.',
  meta: { trace_id: 'auth-123', latency: '45ms' }
};

// 2. Auth Session (Final JWT)
const authSession = {
  status: 'success',
  data: {
    access_token: 'final_jwt_standard_roles_v8',
    company_id: 'c1',
    user: {
      id: 'u-789',
      email: 'demo@interno.core',
      full_name: 'Charly Developer',
      is_active: true
    },
    roles: ['Admin'],
    permissions: [
      'admin:all',
      'inventory:view',
      'inventory:create',
      'inventory:documents',
      'dashboard:view',
      'kardex:view'
    ]
  },
  message: 'Tenant context established.',
  meta: { trace_id: 'session-456', latency: '20ms' }
};

// 3. Products List (Inventory)
const productsList = {
  status: 'success',
  data: [
    {
      id: 'p1',
      company_id: 'c1',
      name: 'Bobina de Acero 2mm',
      sku: 'STEEL-B-001',
      product_type: 'GOODS',
      status: 'ACTIVE',
      version_id: 1,
      is_active: true,
      created_at: new Date().toISOString()
    },
    {
      id: 'p2',
      company_id: 'c1',
      name: 'Viga Industrial H-12',
      sku: 'V-IND-H12',
      product_type: 'GOODS',
      status: 'ACTIVE',
      version_id: 2,
      is_active: true,
      created_at: new Date().toISOString()
    }
  ],
  message: 'Products retrieved successfully',
  meta: { trace_id: 'inv-789', latency: '120ms' }
};

fs.writeFileSync(path.join(mockDir, 'login_handshake.json'), JSON.stringify(loginHandshake, null, 2));
fs.writeFileSync(path.join(mockDir, 'auth_session.json'), JSON.stringify(authSession, null, 2));
fs.writeFileSync(path.join(mockDir, 'products_list.json'), JSON.stringify(productsList, null, 2));

console.log('Mocks generated successfully in docs/specs/mock_responses/');
