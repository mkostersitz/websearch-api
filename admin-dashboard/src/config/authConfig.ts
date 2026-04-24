import { WebStorageStateStore } from 'oidc-client-ts';
import type { AuthProviderProps } from 'react-oidc-context';

const KEYCLOAK_URL = import.meta.env.VITE_KEYCLOAK_URL || '';
const KEYCLOAK_REALM = import.meta.env.VITE_KEYCLOAK_REALM || 'websearch';
const CLIENT_ID = import.meta.env.VITE_KEYCLOAK_CLIENT_ID || '';

export const oidcConfig: AuthProviderProps = {
  authority: `${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}`,
  client_id: CLIENT_ID,
  redirect_uri: window.location.origin + '/auth/callback',
  post_logout_redirect_uri: window.location.origin,
  response_type: 'code',
  scope: 'openid profile email roles',
  userStore: new WebStorageStateStore({ store: window.localStorage }),
  // Skip OIDC provider discovery when not configured
  automaticSilentRenew: !!KEYCLOAK_URL,
};

export const isKeycloakConfigured = !!KEYCLOAK_URL && !!CLIENT_ID;
