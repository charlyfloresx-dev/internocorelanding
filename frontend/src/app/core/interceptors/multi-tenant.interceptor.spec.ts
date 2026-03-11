import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { HttpClient, HttpInterceptorFn, provideHttpClient, withInterceptors } from '@angular/common/http';
import { multiTenantInterceptor } from './multi-tenant.interceptor';
import { AuthService } from '@services/auth.service';

describe('multiTenantInterceptor', () => {
    let httpMock: HttpTestingController;
    let httpClient: HttpClient;
    let authServiceSpy: jasmine.SpyObj<AuthService>;

    beforeEach(() => {
        const spy = jasmine.createSpyObj('AuthService', ['currentContext', 'activeCompanyId']);

        TestBed.configureTestingModule({
            imports: [HttpClientTestingModule],
            providers: [
                { provide: AuthService, useValue: spy },
                provideHttpClient(withInterceptors([multiTenantInterceptor]))
            ]
        });

        httpMock = TestBed.inject(HttpTestingController);
        httpClient = TestBed.inject(HttpClient);
        authServiceSpy = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
    });

    afterEach(() => {
        httpMock.verify();
    });

    it('should inject x-company-id header if companyId is available', () => {
        authServiceSpy.currentContext.and.returnValue({ companyId: 'company-123' } as any);

        httpClient.get('/api/test').subscribe();

        const req = httpMock.expectOne('/api/test');
        expect(req.request.headers.has('x-company-id')).toBe(true);
        expect(req.request.headers.get('x-company-id')).toBe('company-123');
    });

    it('should NOT inject x-company-id header if route is /auth/login', () => {
        authServiceSpy.currentContext.and.returnValue({ companyId: 'company-123' } as any);

        httpClient.post('/api/auth/login', {}).subscribe();

        const req = httpMock.expectOne('/api/auth/login');
        expect(req.request.headers.has('x-company-id')).toBe(false);
    });

    it('should NOT inject x-company-id header if route is /auth/select-company', () => {
        authServiceSpy.currentContext.and.returnValue({ companyId: 'company-123' } as any);

        httpClient.post('/api/auth/select-company', {}).subscribe();

        const req = httpMock.expectOne('/api/auth/select-company');
        expect(req.request.headers.has('x-company-id')).toBe(false);
    });

    it('should NOT inject x-company-id header if no companyId is available', () => {
        authServiceSpy.currentContext.and.returnValue(null);
        authServiceSpy.activeCompanyId.and.returnValue(null);

        httpClient.get('/api/test').subscribe();

        const req = httpMock.expectOne('/api/test');
        expect(req.request.headers.has('x-company-id')).toBe(false);
    });
});
