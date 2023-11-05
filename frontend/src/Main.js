import { Button, Center, Heading, Input, Text } from '@chakra-ui/react';
import React, { useEffect, useState } from 'react';

const Pages = {
    SPLASH: "splash",
    PATIENT: "patient",
    PROVIDER: "provider"
}

const Main = () => {

    

    const [emailField, setEmailField] = useState("");
    const [passwordField, setPasswordField] = useState("");

    const [page, setPage] = useState(Pages.SPLASH);

    const [isLoggedInProvider, setIsLoggedInProvider] = useState(false);
    const [providerInfo, setProviderInfo] = useState({});
    const [isLoggedInPatient, setIsLoggedInPatient] = useState(false);
    const [patientInfo, setPatientInfo] = useState({});

    function emailChange(event) {
        setEmailField(event.target.value);
    }

    function passwordChange(event) {
        setPasswordField(event.target.value);
    }

    function login() {
        await fetch("/api/provider/token", {method: "POST", headers: {"Content-Type": "application/json"}, body: {username: emailField, password: passwordField}})
    }

    useEffect(async () => {
        const providerToken = localStorage.getItem("HA-providertoken");
        if(providerToken) {
            const resp = await fetch(`/api/provider/me`, {
                method: "POST",
                headers: {
                    "Authorization": "Bearer " + providerToken
                }
            })
            if(resp.status == 200) {
                setProviderInfo(await resp.json());
                setIsLoggedInProvider(true);
            }
            else {
                localStorage.removeItem("HA-providertoken")
            }
        }

        const patientToken = localStorage.getItem("HA-patienttoken");
        if(patientToken) {
            const resp = await fetch(`/api/patient/me`, {
                method: "POST",
                headers: {
                    "Authorization": "Bearer " + patientToken
                }
            })
            if(resp.status == 200) {
                setPatientInfo(await resp.json());
                setIsLoggedInPatient(true);
            }
            else {
                localStorage.removeItem("HA-patienttoken")
            }
        }
    }, []);

    return <>
        <Heading>HelpAlign</Heading>
        <Heading as='h4' size='md'>Aligning you with your care</Heading>
        {page === Pages.SPLASH && 
        <Center>
            <Text>Hello!</Text>
            <Text>Are visiting as a:</Text>
            <Button>Patient</Button>
            <Text>or a</Text>
            <Button>Care Provider</Button>
        </Center>
        }
        {page === Pages.PATIENT &&
        <Center>
            {isLoggedInPatient ? <>
            <Text>Hello, {patientInfo.name}</Text>
            <Text>Enter an address to get providers in your area!</Text>
            <Text>Use the buttons to select your preferences</Text>
            </>
            :
            <>
            <Text>Please Enter Your Email and Password:</Text>
            <Input placeholder="Email" onChange={setEmailField} />
            <Input placeholder="Password" onChange={setPasswordField} />
            <Button onClick={login} />
            </>
            }
        </Center>
        }
        
    </>
}

export default Main;