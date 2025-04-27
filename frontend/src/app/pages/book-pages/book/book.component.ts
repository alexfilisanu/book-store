import {Component} from '@angular/core';
import {StarRatingComponent} from "../../../components/star-rating/star-rating.component";
import {BookService} from "../book.service";
import {ActivatedRoute} from "@angular/router";
import {NgIf} from "@angular/common";

@Component({
  selector: 'app-book',
  standalone: true,
  imports: [
    StarRatingComponent,
    NgIf
  ],
  templateUrl: './book.component.html',
  styleUrl: './book.component.css'
})
export class BookComponent {

  public book: any = {};
  public selectedReview: number | null = null;
  public bookRating: number | null = null;
  public addedToCart: boolean = false;

  constructor(private bookService: BookService, private route: ActivatedRoute) {
  }

  ngOnInit(): void {
    this.route.queryParams.subscribe(params => {
      const {isbn = ''} = params;
      this.getBook(isbn);
      this.checkReviewStatus(isbn);
      this.checkIfInCart(isbn);
    })
  }

  private getBook(isbn: string): void {
    this.bookService.getBook(isbn).subscribe({
      next: (response) => {
        this.book = response.book;
      },
      error: (error) => {
        console.error(`Error fetching book with ISBN ${isbn}`, error);
      }
    });
  }

  public addToCart(): void {
    const data = {isbn: this.book.ISBN};
    this.bookService.addToCart(data).subscribe({
      next: () => {
        this.addedToCart = true;
      },
      error: (error) => {
        console.error('Failed to add to cart:', error);
      }
    });
  }

  private checkIfInCart(isbn: string): void {
    this.bookService.checkIfInCart(isbn).subscribe({
      next: (response) => {
        this.addedToCart = response.inCart;
      },
      error: (error) => {
        console.error('Error checking cart status:', error);
      }
    })
  };

  public removeFromCart(): void {
    const data = {isbn: this.book.ISBN};
    this.bookService.removeFromCart(data).subscribe({
      next: () => {
        this.addedToCart = false;
      },
      error: (error) => {
        console.error('Failed to remove from cart:', error);
      }
    });
  }

  private checkReviewStatus(isbn: string): void {
    this.bookService.checkReviewStatus(isbn).subscribe({
      next: (response) => {
        this.bookRating = response.bookRating;
      },
      error: (error) => {
        console.error(`Error checking review status for book ${isbn}`, error);
      }
    });
  }

  public getRating(ratingStr: string): number {
    const rating = parseFloat(ratingStr);
    const roundedRating = Math.round(rating);
    return roundedRating / 2;
  }

  public sendReview(): void {
    if (!this.selectedReview) {
      console.error('No review selected');
      return;
    }

    const reviewData = {isbn: this.book.ISBN, rating: this.selectedReview.toString()};
    this.bookService.submitReview(reviewData).subscribe({
      next: () => {
        window.location.reload();
      },
      error: (error) => {
        console.error('Error submitting review', error);
      }
    });
  }
}
