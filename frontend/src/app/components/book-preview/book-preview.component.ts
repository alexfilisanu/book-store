import {Component, Input} from '@angular/core';
import {Router} from "@angular/router";
import {StarRatingComponent} from "../star-rating/star-rating.component";

@Component({
  selector: 'app-book-preview',
  standalone: true,
  imports: [
    StarRatingComponent
  ],
  templateUrl: './book-preview.component.html',
  styleUrl: './book-preview.component.css'
})
export class BookPreviewComponent {

  @Input() book: any;

  constructor(private router: Router) {
  }

  public getRating(ratingStr: string): number {
    const rating = parseFloat(ratingStr);
    const roundedRating = Math.round(rating);
    return roundedRating / 2;
  }

  public viewBookDetails(): void {
    const role = sessionStorage.getItem('role') ?? 'user';

    this.router.navigate(role === 'admin' ? ['/admin/book'] : ['/book'], {queryParams: {isbn: this.book.ISBN}})
      .catch(error => console.error('Error navigating to book details:', error));
  }
}
