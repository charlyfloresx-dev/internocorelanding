import os
from typing import Tuple, Dict, Any, List
from fido2.server import Fido2Server
from fido2.webauthn import PublicKeyCredentialRpEntity, PublicKeyCredentialUserEntity, AttestedCredentialData, AuthenticatorData
from fido2.utils import websafe_encode, websafe_decode
from auth_app.core.config import settings

# Configuración del Relying Party usando el central config
RP_ID = settings.WEBAUTHN_RP_ID
RP_NAME = settings.WEBAUTHN_RP_NAME
RP_ORIGIN = settings.WEBAUTHN_ORIGIN

class BiometricService:
    def __init__(self):
        # Entidad Relying Party (Nuestra App)
        self.rp = PublicKeyCredentialRpEntity(id=RP_ID, name=RP_NAME)
        self.server = Fido2Server(self.rp)

    def register_begin(self, user_id: bytes, user_email: str, user_name: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Paso 1 del Registro: Inicia el proceso de creación de credencial biométrica.
        Retorna las opciones para el cliente (navigator.credentials.create) y el estado a guardar.
        """
        user = PublicKeyCredentialUserEntity(
            id=user_id,
            name=user_email,
            display_name=user_name
        )
        # credentials=[] porque es un nuevo registro
        registration_data, state = self.server.register_begin(
            user=user,
            credentials=[],
            user_verification="required",
            authenticator_attachment="platform" # Fuerza biométricos del dispositivo (TouchID/FaceID)
        )
        return dict(registration_data), state

    def register_complete(self, state: dict, client_response: dict) -> bytes:
        """
        Paso 2 del Registro: Valida la respuesta del dispositivo y extrae la llave pública.
        Retorna los bytes de la credencial (public_key) para guardar en la DB.
        """
        auth_data = self.server.register_complete(
            state, 
            client_response
        )
        # Retornamos la credencial cruda para guardarla en UserCredential.public_key
        return auth_data.credential_data

    def authenticate_begin(self, allowed_credentials: List[bytes]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Paso 1 del Login: Inicia el proceso de autenticación enviando el challenge.
        allowed_credentials es una lista de public_keys obtenidas de la DB para ese usuario.
        """
        # Rehidratamos las credenciales almacenadas
        credentials = [AttestedCredentialData(cred) for cred in allowed_credentials]
        
        auth_data, state = self.server.authenticate_begin(
            credentials=credentials,
            user_verification="required"
        )
        return dict(auth_data), state

    def authenticate_complete(self, state: dict, credentials: List[bytes], client_response: dict) -> bool:
        """
        Paso 2 del Login: Verifica la firma criptográfica usando la llave pública.
        Si la firma es matemáticamente válida, retorna True.
        """
        try:
            stored_credentials = [AttestedCredentialData(cred) for cred in credentials]
            self.server.authenticate_complete(
                state,
                credentials=stored_credentials,
                response=client_response
            )
            return True
        except Exception as e:
            # Fallo en la validación criptográfica (challenge no coincide, firma inválida, etc)
            print(f"Biometric Validation Failed: {e}")
            return False
