import {Component} from '@angular/core';
import {StarRatingComponent} from "../../../components/star-rating/star-rating.component";
import {BookService} from "../book.service";
import {ActivatedRoute, Router} from "@angular/router";
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
  public userId: string | null = sessionStorage.getItem('userId');
  public bookRating: number | null = null;
  public addedToCart: boolean = false;

  constructor(private bookService: BookService, private route: ActivatedRoute, private router: Router) {
  }

  ngOnInit(): void {
    this.route.params.subscribe(params => {
      const {isbn} = params;
      this.getBook(isbn);
      this.checkReviewStatus(isbn);
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

  public addToCart(book: any): void {
  if (book.Quantity > 0) {
    console.log(`Added ${book.Book_Title} to cart!`);
    this.addedToCart = true;
    setTimeout(() => this.addedToCart = false, 3000);
  } else {
    console.warn('This book is out of stock!');
  }
}

  private checkReviewStatus(isbn: string): void {
    if (!this.userId) {
      console.error('No user ID found');
      return;
    }

    this.bookService.checkReviewStatus(isbn, this.userId).subscribe({
      next: (response) => {
        this.bookRating = response.bookRating;
      },
      error: (error) => {
        console.error(`Error checking review status for user ${this.userId} and book ${isbn}`, error);
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
    if (!this.userId) {
      console.error('No user ID found');
      return;
    }

    const reviewData = {userId: this.userId, isbn: this.book.ISBN, rating: this.selectedReview.toString()};
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
