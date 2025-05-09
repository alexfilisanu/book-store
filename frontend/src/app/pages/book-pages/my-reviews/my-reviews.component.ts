import {Component} from '@angular/core';
import {BookService} from "../book.service";
import {ActivatedRoute} from "@angular/router";
import {BooksPaginationComponent} from "../../../components/books-pagination/books-pagination.component";

@Component({
  selector: 'app-my-reviews',
  imports: [
    BooksPaginationComponent
  ],
  templateUrl: './my-reviews.component.html',
  standalone: true,
  styleUrl: './my-reviews.component.css'
})
export class MyReviewsComponent {

  public userName: string | null = sessionStorage.getItem('username');
  public reviews: any[] = [];
  public currentPage: number = 1;
  public totalReviews: number = 0;
  public totalPages: number = 0;
  private booksPerPage: number = 4;

  constructor(private bookService: BookService, private route: ActivatedRoute) {
  }

  ngOnInit(): void {
    this.route.queryParams.subscribe(() => {
      this.currentPage = 1;
      this.getTotalBooks();
      this.getBooks();
    });
  }

  private getTotalBooks(): void {
    this.bookService.getMyTotalReviews().subscribe({
      next: (response) => {
        this.totalReviews = response.totalReviews;
        this.totalPages = Math.ceil(this.totalReviews / this.booksPerPage);
      },
      error: (error) => {
        console.error('Error fetching my total reviews', error);
      }
    });
  }

  private getBooks(page: number = this.currentPage): void {
    this.bookService.getMyReviews(page, this.booksPerPage).subscribe({
      next: (response) => {
        this.reviews = response.reviews;
      },
      error: (error) => {
        console.error(`Error fetching books for page ${page}`, error);
      }
    });
  }

  public onPageChange(newPage: number): void {
    this.currentPage = newPage;
    this.getBooks();
  }
}
