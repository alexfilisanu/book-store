import {Component} from '@angular/core';
import {ReactiveFormsModule} from "@angular/forms";
import {Router} from "@angular/router";

@Component({
  selector: 'app-admin-navbar',
  imports: [
    ReactiveFormsModule
  ],
  templateUrl: './admin-navbar.component.html',
  styleUrl: './admin-navbar.component.css'
})
export class AdminNavbarComponent {

  constructor(private router: Router) {
  }

  public logout(): void {
    sessionStorage.clear();
    this.navigatePage('login');
  }

  public navigatePage(page: string): void {
    this.router.navigate([`/${page}`])
      .catch(error => console.error(`Error navigating to ${page}:`, error));
  }
}
