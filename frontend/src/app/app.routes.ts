import {Routes} from '@angular/router';
import {UserLayoutComponent} from "./components/user-layout/user-layout.component";
import {BooksComponent} from "./pages/book-pages/books/books.component";
import {BookComponent} from "./pages/book-pages/book/book.component";
import {LoginComponent} from "./pages/auth/login/login.component";
import {RegisterComponent} from "./pages/auth/register/register.component";
import {NotFoundComponent} from "./pages/not-found/not-found.component";
import {MyReviewsComponent} from "./pages/book-pages/my-reviews/my-reviews.component";
import {MyCartComponent} from "./pages/book-pages/my-cart/my-cart.component";
import {DashboardComponent} from "./pages/admin/dashboard/dashboard.component";
import {BookManagementComponent} from "./pages/admin/book-management/book-management.component";
import {StatisticsComponent} from "./pages/admin/statistics/statistics.component";
import {AdminLayoutComponent} from "./components/admin-layout/admin-layout.component";
import {AdminBookComponent} from "./pages/admin/admin-book/admin-book.component";
import {AdminAddBookComponent} from "./pages/admin/admin-add-book/admin-add-book.component";

export const routes: Routes = [
  {
    path: 'login',
    component: LoginComponent
  },
  {
    path: 'register',
    component: RegisterComponent
  },
  {
    path: '',
    redirectTo: 'login',
    pathMatch: 'full'
  },
  {
    path: 'admin',
    component: AdminLayoutComponent,
    children: [
      {
        path: 'dashboard',
        component: DashboardComponent
      },
      {
        path: 'books',
        component: BookManagementComponent
      },
      {
        path: 'book/:isbn',
        component: AdminBookComponent
      },
      {
        path: 'add-book',
        component: AdminAddBookComponent
      },
      {
        path: 'stats',
        component: StatisticsComponent
      }
    ]
  },
  {
    path: '',
    component: UserLayoutComponent,
    children: [
      {
        path: 'books',
        component: BooksComponent
      },
      {
        path: 'book/:isbn',
        component: BookComponent
      },
      {
        path: 'my-reviews',
        component: MyReviewsComponent
      },
      {
        path: 'my-cart',
        component: MyCartComponent
      }
    ]
  },
  {
    path: '**',
    component: NotFoundComponent
  }
];
