import {Injectable} from '@angular/core';
import {HttpClient, HttpHeaders, HttpParams} from "@angular/common/http";
import {catchError, Observable, switchMap, throwError, of} from "rxjs";

@Injectable({
  providedIn: 'root'
})
export class BookService {

  private baseUrl = 'http://localhost:3050';

  constructor(private http: HttpClient) {
  }

  private requestWithRefresh<T>(request: (headers: HttpHeaders) => Observable<T>): Observable<T> {
    const token = sessionStorage.getItem('access_token');
    const refreshToken = sessionStorage.getItem('refresh_token');

    let headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);

    return request(headers).pipe(
      catchError((error) => {
        if (error.status === 401 && refreshToken) {
          return this.refreshAccessToken(refreshToken).pipe(
            switchMap((newAccessToken) => {
              sessionStorage.setItem('access_token', newAccessToken);
              headers = new HttpHeaders().set('Authorization', `Bearer ${newAccessToken}`);
              return request(headers);
            })
          );
        } else {
          return throwError(() => error);
        }
      })
    );
  }

  public getTotalBooks(query: string): Observable<any> {
    return this.requestWithRefresh((headers) => {
      const params = new HttpParams()
        .set('q', query);

      return this.http.get<any>(`${this.baseUrl}/total-books`, {headers, params});
    });
  }

  public getBooks(query: string, page: number = 1, limit: number = 10): Observable<any> {
    const params = new HttpParams()
      .set('q', query)
      .set('page', page.toString())
      .set('limit', limit.toString());

    return this.requestWithRefresh((headers) =>
      this.http.get<any>(`${this.baseUrl}/books`, {headers, params})
    );
  }

  public getBook(isbn: string): Observable<any> {
    const params = new HttpParams()
      .set('isbn', isbn)

    return this.requestWithRefresh((headers) =>
      this.http.get<any>(`${this.baseUrl}/book`, {headers, params})
    );
  }

  public getMyTotalReviews(): Observable<any> {
    return this.requestWithRefresh((headers) =>
      this.http.get<any>(`${this.baseUrl}/total-reviews`, {headers})
    );
  }

  public getMyReviews(page: number = 1, limit: number = 10): Observable<any> {
    const params = new HttpParams()
      .set('page', page.toString())
      .set('limit', limit.toString());

    return this.requestWithRefresh((headers) =>
      this.http.get<any>(`${this.baseUrl}/reviews`, {headers, params})
    );
  }

  public checkReviewStatus(isbn: string): Observable<any> {
    const params = new HttpParams()
      .set('isbn', isbn);

    return this.requestWithRefresh((headers) =>
      this.http.get<any>(`${this.baseUrl}/book/review/status`, {headers, params})
    );
  }

  public submitReview(reviewData: any): Observable<any> {
    return this.requestWithRefresh((headers) =>
      this.http.post<any>(`${this.baseUrl}/book/review`, reviewData, {headers})
    );
  }

  public addToCart(data: any): Observable<any> {
    return this.requestWithRefresh((headers) =>
      this.http.post<any>(`${this.baseUrl}/cart`, data, {headers})
    );
  }

  public removeFromCart(data: any): Observable<any> {
    return this.requestWithRefresh((headers) =>
      this.http.request<any>('delete', `${this.baseUrl}/cart`, {headers, body: data})
    );
  }

  public getMyTotalBooksCart(): Observable<any> {
    return this.requestWithRefresh((headers) =>
      this.http.get<any>(`${this.baseUrl}/total-cart`, {headers})
    );
  }

  public getMyBooksCart(page: number = 1, limit: number = 10): Observable<any> {
    const params = new HttpParams()
      .set('page', page.toString())
      .set('limit', limit.toString());

    return this.requestWithRefresh((headers) =>
      this.http.get<any>(`${this.baseUrl}/cart`, {headers, params})
    );
  }

  public getAllBooksCart(): Observable<any> {
    return this.requestWithRefresh((headers) =>
      this.http.get<any>(`${this.baseUrl}/cart`, {headers})
    );
  }

  public checkIfInCart(isbn: string): Observable<{ inCart: boolean }> {
    const params = new HttpParams()
      .set('isbn', isbn);

    return this.requestWithRefresh((headers) =>
      this.http.get<{ inCart: boolean }>(`${this.baseUrl}/cart/check`, {headers, params})
    );
  }

  public orderBooks(data: any): Observable<any> {
    return this.requestWithRefresh((headers) =>
      this.http.post<any>(`${this.baseUrl}/order`, data, {headers})
    );
  }

  public addBook(data: any): Observable<any> {
    return this.requestWithRefresh((headers) =>
      this.http.post<any>(`${this.baseUrl}/admin/book`, data, {headers})
    );
  }

  public updateBook(data: any): Observable<any> {
    return this.requestWithRefresh((headers) =>
      this.http.put<any>(`${this.baseUrl}/admin/book`, data, {headers})
    );
  }

  public deleteBook(isbn: string): Observable<any> {
    const params = new HttpParams()
      .set('isbn', isbn);

    return this.requestWithRefresh((headers) =>
      this.http.delete<any>(`${this.baseUrl}/admin/book`, {headers, params})
    );
  }

  public getOrdersPerMonth(year: number): Observable<any> {
    const params = new HttpParams()
      .set('year', year.toString());

    return this.requestWithRefresh((headers) =>
      this.http.get<any>(`${this.baseUrl}/stats/orders-per-month`, {headers, params})
    );
  }

  public getEarningsPerMonth(year: number): Observable<any> {
    const params = new HttpParams()
      .set('year', year.toString());

    return this.requestWithRefresh((headers) =>
      this.http.get<any>(`${this.baseUrl}/stats/earnings-per-month`, {headers, params})
    );
  }

  public getPublisherDistribution(): Observable<any> {
    return this.requestWithRefresh((headers) =>
      this.http.get<any>(`${this.baseUrl}/stats/publisher-distribution`, {headers})
    );
  }

  private refreshAccessToken(refreshToken: string): Observable<string> {
    return this.http.post<any>('http://localhost:3100/auth/refresh', {refresh_token: refreshToken}).pipe(
      switchMap((response) => {
        if (response.access_token) {
          return of(response.access_token);
        } else {
          throw new Error('Refresh token invalid');
        }
      })
    );
  }
}
