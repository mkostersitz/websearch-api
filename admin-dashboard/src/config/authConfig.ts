/**
 * OIDC Configuration for Keycloak
 */

import { WebStorageStateStore } from 'oidc-client-ts';
import type { AuthProviderProps } from 'react-oidc-context';

export const KEYCLOAK_URL =
  import.meta.env.VITE_KEYCLOAK_URL || 'http://keycloak.local';
export const KEYCLOAK_REALM =
  import.meta.env.VITE_KEYCLOAK_REALM || 'websearch';
export const CLIENT_ID =
  import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'websearch-dashboard';

export const oidcConfig: AuthProviderProps = {
  authority: `${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}`,
  client_id: CLIENT_ID,
  redirect_uri: window.location.origin + '/auth/callback',
  post_logout_redirect_uri: window.location.origin,
  response_type: 'code',
  scope: 'openid profile email roles',
  userStore: new WebStorageStateStore({ store: window.localStorage }),
  automaticSilentRenew: true,
  onSigninCallback: () => {
    // Strip OIDC query params from the URL after login redirect
    window.history.replaceState({}, document.title, window.location.pathname);
  },
};

export const isKeycloakConfigured = !!KEYCLOAK_URL && !!CLIENT_ID;
