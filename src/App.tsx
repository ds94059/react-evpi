import React from 'react';
import logo from './logo.svg';
import './App.css';
import { Button, Card, Spinner } from 'react-bootstrap';
import { Check } from 'react-bootstrap-icons';
import { useState, useEffect } from 'react';

import 'bootstrap/dist/css/bootstrap.min.css';

let updateId: NodeJS.Timeout;

function App() {

  useEffect(() => {
    updateId = setInterval(() => {
      // console.log("check for update...")
      let newUpdate = false;
      //fetch=================

      //=====================
      if (newUpdate) {
        //todo

        clearInterval(updateId);
      }

    }, 3000)
  })

  const clickUpdate = () => {
    console.log('Updating...')

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
        <Spinner animation="border" role="status" style={{ color: '#ffffff' }}>
          <span className="visually-hidden">Loading...</span>
        </Spinner>
        <Card>
          <Check color='Green' size={96} />
        </Card>
        <Button variant='warning' onClick={clickUpdate}>
          Update
        </Button>
      </header>
    </div >
  );
}

export default App;
