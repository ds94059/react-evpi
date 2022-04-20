import './App.css';
import { Button, Card, Spinner } from 'react-bootstrap';
import { Check } from 'react-bootstrap-icons';
import { useState, useEffect } from 'react';
import webSocket from "socket.io-client"

import 'bootstrap/dist/css/bootstrap.min.css';

const endPoint = "http://127.0.0.1:5000";
let JWT = "";
let newUpdate = false;

let updateId: NodeJS.Timeout;

function App() {
	const socket = webSocket(endPoint);
	const [isUpdating, setIsUpdating] = useState(false);
	const [isNewUpdate, setIsNewUpdate] = useState(false);

	useEffect(() => loginToMender, [])

	const loginToMender = () => {
		clearInterval(updateId);
		if (socket) {
			console.log('connect success');
			socket.on('JWT', msg => {
				JWT = msg
				console.log(JWT)
				if (JWT) {
					console.log('login success')
					updateId = setInterval(() => {
						if (!newUpdate)
							checkUpdate();
					}, 10000)
				}
				else
					console.log('login failed')
			})
			socket.emit('message', 'login');
			console.log('login...')
		}
		else
			console.log('connect failed')
	}

	const clickUpdate = () => {
		console.log('Updating...')
		setIsUpdating(true);
		socket.emit('message', 'continue');
		setTimeout(() => {
			socket.emit('message', 'pause');
			console.log('pause installing');
			newUpdate = false;
			setIsUpdating(false);
			setIsNewUpdate(false);
		}, 10000)
	}

	const checkUpdate = () => {
		console.log("check for update...")
		socket.emit('checkUpdate', JWT);
		socket.on('update', msg => {
			if (msg === 'true') {
				newUpdate = true;
				setIsNewUpdate(true);
				console.log('new update')
			}
			else {
				newUpdate = false;
				setIsNewUpdate(false);
			}
		})
	}

	return (
		<div className="App">
			<header className="App-header">
				{/* <img src={logo} className="App-logo" alt="logo" />
        <p>
          Edit <code>src/App.tsx</code> and save to reload.nooooo
        </p>
        <Button variant='danger'>
          Primary
        </Button>
        <Card>
          <Card.Body style={{ color: "#000000" }}>This is some text within a card body.</Card.Body>
        </Card>
        <a
          className="App-link"
          href="https://reactjs.org"
          target="_blank"
          rel="noopener noreferrer"
        >
          Learn React
        </a> */}
				{/* <Spinner animation="border" role="status" style={{ color: '#ffffff' }}>
					<span className="visually-hidden">Loading...</span>
				</Spinner> */}
				<Card style={{ 'alignItems': 'center' }}>
					Latest version
					<Check color='Green' size={96} />
				</Card>
				<Button
					variant='warning'
					onClick={clickUpdate}
					disabled={isUpdating || !isNewUpdate}
				>
					{isUpdating ? 'Updating...' : 'Update'}
				</Button>
			</header>
		</div >
	);
}

export default App;
