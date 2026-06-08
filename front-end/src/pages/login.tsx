import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { KeyRound, LogIn } from 'lucide-react'
import { useAuth } from '../auth/auth-context'
import { Button } from '../ui/button'

const sampleCustomer = 'Bearer user:user-1'
const sampleStaff = 'Bearer staff:staff-1;roles=ADMIN;permissions=product:create,product:update,order:read,staff:read,role:read,shipping:manage,comment:moderate'

export function LoginPage() {
  const auth = useAuth()
  const navigate = useNavigate()
  const [token, setToken] = useState(sampleCustomer)

  function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    auth.loginToken(token)
    navigate(token.includes('staff:') ? '/admin' : '/products')
  }

  return (
    <main className="center-panel login-panel">
      <KeyRound size={32} aria-hidden="true" />
      <h1>Login</h1>
      <form className="stack" onSubmit={submit}>
        <label>
          Access token
          <textarea value={token} onChange={(event) => setToken(event.target.value)} rows={4} />
        </label>
        <div className="segmented">
          <Button variant="secondary" onClick={() => setToken(sampleCustomer)}>
            Customer
          </Button>
          <Button variant="secondary" onClick={() => setToken(sampleStaff)}>
            Staff
          </Button>
        </div>
        <Button type="submit">
          <LogIn size={17} aria-hidden="true" />
          Continue
        </Button>
      </form>
    </main>
  )
}
