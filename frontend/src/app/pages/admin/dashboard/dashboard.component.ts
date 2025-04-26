import {Component} from '@angular/core';
import {Router} from "@angular/router";

@Component({
  selector: 'app-dashboard',
  imports: [],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css'
})
export class DashboardComponent {

  constructor(private router: Router) {
  }

  public navigatePage(page: string): void {
    this.router.navigate([`/${page}`])
      .catch(error => console.error(`Error navigating to ${page}:`, error));
  }
}
