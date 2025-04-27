import {Component} from '@angular/core';
import {BookService} from "../../book-pages/book.service";
import {ActivatedRoute, Router} from "@angular/router";
import {FormBuilder, FormGroup, ReactiveFormsModule, Validators} from "@angular/forms";

@Component({
  selector: 'app-admin-book',
  imports: [
    ReactiveFormsModule
  ],
  templateUrl: './admin-book.component.html',
  styleUrl: './admin-book.component.css'
})
export class AdminBookComponent {

  public book: any = {};
  public bookRating: number | null = null;
  public bookForm!: FormGroup;

  constructor(private formBuilder: FormBuilder, private bookService: BookService, private route: ActivatedRoute, private router: Router) {
    this.bookForm = this.formBuilder.group({
      quantity: [this.book.Quantity, Validators.min(0)],
      price: [this.book.Price, Validators.min(0)],
    });
  }

  ngOnInit(): void {
    this.route.queryParams.subscribe(params => {
      const {isbn = ''} = params;
      this.getBook(isbn);
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

  public deleteBook(): void {
    const isbn = this.book.ISBN;

    this.bookService.deleteBook(isbn).subscribe({
      next: () => {
        this.router.navigate(['/admin/books']).catch(error => {
          console.error('Error navigating to book management:', error);
        });
      },
      error: (error) => {
        console.error(`Error deleting book with ISBN ${isbn}`, error);
      }
    });
  }

  public onSubmit(): void {
    if (this.bookForm.valid) {
      const updatedBook = {
        isbn: this.book.ISBN,
        price: this.bookForm.value.price,
        quantity: this.bookForm.value.quantity
      };

      this.bookService.updateBook(updatedBook).subscribe({
        next: () => {
          this.getBook(this.book.ISBN);
        },
        error: (error: any) => {
          console.error('Error updating book:', error);
        }
      });
    } else {
      console.error('Form is invalid');
    }
  }
}
