import {Component} from '@angular/core';
import {BooksPaginationComponent} from "../../../components/books-pagination/books-pagination.component";
import {BookService} from "../book.service";
import {ActivatedRoute} from "@angular/router";
import {FormBuilder, ReactiveFormsModule, Validators} from "@angular/forms";

@Component({
  selector: 'app-my-cart',
  imports: [
    BooksPaginationComponent,
    ReactiveFormsModule
  ],
  templateUrl: './my-cart.component.html',
  styleUrl: './my-cart.component.css'
})
export class MyCartComponent {

  public orderFormGroup: any;
  public userId: string | null = sessionStorage.getItem('userId');
  public booksCart: any[] = [];
  public currentPage: number = 1;
  public totalBooksCart: number = 0;
  public totalPages: number = 0;
  private booksPerPage: number = 4;

  constructor(private formBuilder: FormBuilder, private bookService: BookService, private route: ActivatedRoute) {
  }

  ngOnInit(): void {
    this.route.queryParams.subscribe(() => {
      this.currentPage = 1;
      this.getTotalBooks();
      this.getBooks();
    });
    this.orderFormGroup = this.formBuilder.group({
      address: ['', Validators.required]
    });
  }

  public onSubmit(): void {
    if (this.orderFormGroup?.valid && this.userId) {
      const address = this.orderFormGroup.get('address')?.value;

      this.bookService.getAllBooksCart(this.userId).subscribe({
        next: (response) => {
          const allBooks: any[] = response.booksCart;
          const orderData = {
            userId: this.userId,
            address: address,
            items: allBooks.map(book => ({
              isbn: book.ISBN
            }))
          };

          this.bookService.orderBooks(orderData).subscribe({
            next: () => {
              this.booksCart = [];
              this.totalBooksCart = 0;
              this.totalPages = 0;
            },
            error: err => {
              console.error('Error placing order:', err);
            }
          });
        },
        error: (err) => {
          console.error('Error fetching all books from cart:', err);
        }
      });
    }
  }

  private getTotalBooks(): void {
    if (!this.userId) {
      console.error('User ID is not available');
      return;
    }

    this.bookService.getMyTotalBooksCart(this.userId).subscribe({
      next: (response) => {
        this.totalBooksCart = response.totalBooksCart;
        this.totalPages = Math.ceil(this.totalBooksCart / this.booksPerPage);
      },
      error: (error) => {
        console.error('Error fetching my total books cart', error);
      }
    });
  }

  private getBooks(page: number = this.currentPage): void {
    if (!this.userId) {
      console.error('User ID is not available');
      return;
    }

    this.bookService.getMyBooksCart(this.userId, page, this.booksPerPage).subscribe({
      next: (response) => {
        this.booksCart = response.booksCart;
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
