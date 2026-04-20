import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { HttpClient, HttpErrorResponse, provideHttpClient, withInterceptors } from '@angular/common/http';
import { apiInterceptor } from './api.interceptor';

describe('apiInterceptor', () => {
    let httpMock: HttpTestingController;
    let httpClient: HttpClient;

    beforeEach(() => {
        TestBed.configureTestingModule({
            imports: [HttpClientTestingModule],
            providers: [
                provideHttpClient(withInterceptors([apiInterceptor]))
            ]
        });

        httpMock = TestBed.inject(HttpTestingController);
        httpClient = TestBed.inject(HttpClient);
    });

    afterEach(() => {
        httpMock.verify();
    });

    it('should pass through successful responses', () => {
        const mockResponse = { status: 'success', data: { id: 1 } };

        httpClient.get('/api/data').subscribe(res => {
            expect(res).toEqual(mockResponse);
        });

        const req = httpMock.expectOne('/api/data');
        req.flush(mockResponse);
    });

    it('should throw an error if the status in a 200 OK response is "error"', () => {
        const mockErrorResponse = { status: 'error', message: 'Logic error from backend' };

        httpClient.get('/api/data').subscribe({
            next: () => fail('Should have thrown an error'),
            error: (error: HttpErrorResponse) => {
                expect(error.error).toEqual(mockErrorResponse);
                expect(error.status).toBe(200); // Because we flush with 200
            }
        });

        const req = httpMock.expectOne('/api/data');
        req.flush(mockErrorResponse, { status: 200, statusText: 'OK' });
    });
});
