import {Component} from '@angular/core';
import {ReactiveFormsModule} from "@angular/forms";
import {Location} from '@angular/common';

@Component({
  selector: 'app-not-found',
  standalone: true,
  imports: [
    ReactiveFormsModule
  ],
  templateUrl: './not-found.component.html',
  styleUrl: './not-found.component.css'
})
export class NotFoundComponent {

  constructor(private location: Location) {
  }

  goBack(): void {
    this.location.back();
  }
}
