import {Component} from '@angular/core';
import {FormBuilder, FormsModule, ReactiveFormsModule, Validators} from "@angular/forms";
import {NgClass} from "@angular/common";
import {AuthService} from "../auth.service";
import {Router} from "@angular/router";
import * as jwt_decode from 'jwt-decode';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    FormsModule,
    ReactiveFormsModule,
    NgClass
  ],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css'
})
export class LoginComponent {

  public isVisible: boolean = false;
  public errorMessage: string = '';
  public loginFormGroup: any;

  constructor(private formBuilder: FormBuilder, private authService: AuthService, private router: Router) {
  }

  ngOnInit(): void {
    this.loginFormGroup = this.formBuilder.group({
      username: ['', Validators.required],
      password: ['', Validators.required]
    });
  }

  public togglePassword(): void {
    this.isVisible = !this.isVisible;
  }

  public onSubmit(): void {
    if (this.loginFormGroup?.valid) {
      this.errorMessage = ''

      this.authService.loginUser(this.loginFormGroup.value).subscribe({
        next: (response) => {
          sessionStorage.setItem('access_token', response.access_token);
          sessionStorage.setItem('refresh_token', response.refresh_token);

          const decodedToken: any = jwt_decode.jwtDecode(response.access_token);
          sessionStorage.setItem('username', decodedToken.username);
          sessionStorage.setItem('role', decodedToken.role);

          if (decodedToken.role === 'admin') {
            this.router.navigate(['/admin/dashboard']).catch(error => {
              console.error('Error navigating to admin dashboard:', error);
            });
          } else {
            this.router.navigate(['/books']).catch(error => {
              console.error('Error navigating to user dashboard:', error);
            });
          }
        },
        error: (error) => {
          this.errorMessage = error.error.error;
          console.error('Error occurred while logging in the user:', error);
        }
      })
    } else if (this.areAllFieldsCompleted() && this.loginFormGroup?.get("username").invalid) {
      this.errorMessage = 'Username is invalid';
    } else if (this.areAllFieldsCompleted() && this.loginFormGroup?.get("password").invalid) {
      this.errorMessage = 'Password is invalid';
    } else {
      this.errorMessage = 'All fields are required';
    }
  }

  private areAllFieldsCompleted(): boolean {
    return this.loginFormGroup?.get("username").value
      && this.loginFormGroup?.get("password").value
  }

  public navigateRegister() {
    this.router.navigate([`/register`])
      .catch(error => console.error(`Error navigating to register:`, error));
  }
}
