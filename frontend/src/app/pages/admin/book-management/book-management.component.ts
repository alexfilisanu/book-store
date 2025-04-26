import {Component} from '@angular/core';
import {FormBuilder, FormControl, FormGroup, FormsModule, ReactiveFormsModule} from "@angular/forms";
import {BooksPaginationComponent} from "../../../components/books-pagination/books-pagination.component";
import {BookService} from "../../book-pages/book.service";
import {ActivatedRoute} from "@angular/router";

@Component({
  selector: 'app-book-management',
  imports: [
    FormsModule,
    ReactiveFormsModule,
    BooksPaginationComponent
  ],
  templateUrl: './book-management.component.html',
  styleUrl: './book-management.component.css'
})
export class BookManagementComponent {

  public searchBooksFormGroup!: FormGroup;
  public books: any[] = [];
  public currentPage: number = 1;
  public totalBooks: number = 0;
  public totalPages: number = 0;
  private booksPerPage: number = 4;
  private searchQuery: string = '';

  constructor(private formBuilder: FormBuilder, private bookService: BookService, private route: ActivatedRoute) {
  }

  ngOnInit(): void {
    this.searchBooksFormGroup = this.formBuilder.group({
      searchQuery: new FormControl('')
    });
    this.route.queryParams.subscribe(() => {
      this.currentPage = 1;
      this.getTotalBooks();
      this.getBooks();
    });
  }

  private getTotalBooks(): void {
    this.bookService.getTotalBooks(this.searchQuery).subscribe({
      next: (response) => {
        this.totalBooks = response.totalBooks;
        this.totalPages = Math.ceil(this.totalBooks / this.booksPerPage);
      },
      error: (error) => {
        console.error('Error fetching total books', error);
      }
    });
  }

  private getBooks(page: number = this.currentPage): void {
    this.bookService.getBooks(this.searchQuery, page, this.booksPerPage).subscribe({
      next: (response) => {
        this.books = response.books;
      },
      error: (error) => {
        console.error(`Error fetching books for page ${page}`, error);
      }
    });
  }

  public searchBooks(): void {
    this.searchQuery = this.searchBooksFormGroup.get('searchQuery')?.value;

    if (this.searchQuery.trim()) {
      this.currentPage = 1;
      this.getTotalBooks();
      this.getBooks();
    }
  }

  public onPageChange(newPage: number): void {
    this.currentPage = newPage;
    this.getBooks(this.currentPage);
  }
}
