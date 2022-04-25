import './App.css';
import { Button, Card, Spinner } from 'react-bootstrap';
import * as Icon from 'react-bootstrap-icons';
import { useState, useEffect } from 'react';
import webSocket from "socket.io-client"

import 'bootstrap/dist/css/bootstrap.min.css';

const endPoint = "http://127.0.0.1:5000";
let JWT = "";
let newUpdate = false;
let updating = false;

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
						checkUpdate();
					}, 10000)
				}
				else
					console.log('login failed')
			})
			socket.on('update', msg => {
				if (msg === 'true') {
					setIsNewUpdate(true);
					console.log('new update')
				}
				else {
					updating = false;
					setIsUpdating(false);
					setIsNewUpdate(false);
				}
			})
			socket.emit('message', 'login');
			console.log('login...')
		}
		else
			console.log('connect failed')
	}

	const clickUpdate = () => {
		console.log('Updating...')
		updating = true;
		setIsUpdating(true);
		socket.emit('message', 'continue');
		setTimeout(() => {
			socket.emit('message', 'pause');
			console.log('pause installing');

			socket.emit('message', 'rviz2')
			// newUpdate = false;
			// setIsUpdating(false);
			// setIsNewUpdate(false);
			// socket.emit('message', 'rviz2');
		}, 10000)
	}

	const checkUpdate = () => {
		console.log("check for update...")
		socket.emit('checkUpdate', JWT);
	}
	return (
		<div className="App">
			<header className="App-header">
				{/* <img src={logo} className="App-logo" alt="logo" />
        <p>
          Edit <code>src/App.tsx</code> and save to reload.nooooo
        </p>
        <a
          className="App-link"
          href="https://reactjs.org"
          target="_blank"
          rel="noopener noreferrer"
        >
          Learn React
        </a> */}
				<div className="row-content">
					<Button
						className="rounded-circle circle"
						variant='warning'
						onClick={clickUpdate}
						disabled={isUpdating || !isNewUpdate}
					>
						{
							isUpdating ?
								<Spinner animation="border" role="status" style={{ color: '#ffffff' }}>
									<span className="visually-hidden">Loading...</span>
								</Spinner>
								: isNewUpdate ? 'Update' : <Icon.Check2Circle color='black' size={72} />
						}
					</Button>
				</div>
				<Card style={{ width: '300px', marginTop: '20px' }}>
					<Card.Body>
						{isNewUpdate ?
							isUpdating ? 'Updating...' : 'New update'
							: 'Latest version'}
						{
							isNewUpdate ?
								<Icon.ExclamationCircle color='red' size={36} style={{ marginLeft: '20px' }} /> :
								<Icon.Check color='Green' size={64} />
						}
					</Card.Body>
				</Card>
			</header>
		</div >
	);
}

export default App;
