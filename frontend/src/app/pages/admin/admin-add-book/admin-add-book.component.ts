import { Component } from '@angular/core';
import {FormBuilder, FormGroup, ReactiveFormsModule, Validators} from "@angular/forms";
import {BookService} from "../../book-pages/book.service";
import {Router} from "@angular/router";

@Component({
  selector: 'app-admin-add-book',
  imports: [
    ReactiveFormsModule
  ],
  templateUrl: './admin-add-book.component.html',
  styleUrl: './admin-add-book.component.css'
})
export class AdminAddBookComponent {

  public bookForm!: FormGroup;

  constructor(private formBuilder: FormBuilder, private bookService: BookService, private router: Router) {
    this.bookForm = this.formBuilder.group({
      isbn: ['', [Validators.required]],
      title: ['', Validators.required],
      author: ['', Validators.required],
      year: ['', Validators.required],
      publisher: ['', Validators.required],
      image: ['', Validators.required],
      price: ['', [Validators.required, Validators.min(0)]],
      quantity: ['', [Validators.required, Validators.min(0)]],
    });
  }

  public onSubmit(): void {
    if (this.bookForm.valid) {
      const bookData = this.bookForm.value;

      this.bookService.addBook(bookData).subscribe({
        next: () => {
          this.router.navigate(['/admin/book', bookData.isbn]).catch(error => {
            console.error('Error navigating to book:', error);
          });
          this.bookForm.reset();
        },
        error: (error) => {
          console.error('Error adding book:', error);
        }
      });
    } else {
      console.log('Form is invalid');
    }
  }
}
