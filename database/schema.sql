-- organisation, role, person, person_role

CREATE TABLE organisation (
    id          INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        VARCHAR(150) NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE role (
    role_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    role    VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE person (
    person_id       INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id INT NOT NULL,
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    email           VARCHAR(150) NOT NULL UNIQUE,
    password        VARCHAR(255) NOT NULL,
    phone_number    VARCHAR(50),
    address         VARCHAR(255),
    status          VARCHAR(30),
    date_joined     DATE,
    CONSTRAINT fk_person_organisation
        FOREIGN KEY (organization_id) REFERENCES organisation(id)
);

CREATE TABLE person_role (
    person_id INT NOT NULL,
    role_id   INT NOT NULL,
    PRIMARY KEY (person_id, role_id),
    CONSTRAINT fk_person_role_person
        FOREIGN KEY (person_id) REFERENCES person(person_id),
    CONSTRAINT fk_person_role_role
        FOREIGN KEY (role_id) REFERENCES role(role_id)
);


-- student and staff

CREATE TABLE student (
    person_id       INT PRIMARY KEY,
    subject         VARCHAR(150) NOT NULL,
    enrollment_date DATE NOT NULL,
    student_status  VARCHAR(30),
    CONSTRAINT fk_student_person
        FOREIGN KEY (person_id) REFERENCES person(person_id)
);

CREATE TABLE staff (
    person_id  INT PRIMARY KEY,
    department VARCHAR(150) NOT NULL,
    CONSTRAINT fk_staff_person
        FOREIGN KEY (person_id) REFERENCES person(person_id)
);

-- building, room, it_desk

CREATE TABLE building (
    id              INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organisation_id INT NOT NULL,
    name            VARCHAR(150) NOT NULL,
    status          VARCHAR(30),
    address         VARCHAR(255),
    city            VARCHAR(100),
    postcode        VARCHAR(20),
    country         VARCHAR(100),
    CONSTRAINT fk_building_org
        FOREIGN KEY (organisation_id) REFERENCES organisation(id)
);

CREATE TABLE room (
    id          INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    building_id INT NOT NULL,
    floor       VARCHAR(20),
    status      VARCHAR(30),
    CONSTRAINT fk_room_building
        FOREIGN KEY (building_id) REFERENCES building(id)
);

CREATE TABLE it_desk (
    id          INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    building_id INT NOT NULL,
    status      VARCHAR(30),
    floor       VARCHAR(20),
    CONSTRAINT fk_desk_building
        FOREIGN KEY (building_id) REFERENCES building(id)
);

-- it_technician (staff + desk)

CREATE TABLE it_technician (
    person_id      INT PRIMARY KEY,
    desk_id        INT NOT NULL,
    status         VARCHAR(30),
    specialization VARCHAR(150),
    CONSTRAINT fk_ittech_staff
        FOREIGN KEY (person_id) REFERENCES staff(person_id),
    CONSTRAINT fk_ittech_desk
        FOREIGN KEY (desk_id) REFERENCES it_desk(id)
);

-- device and subtypes

CREATE TABLE device (
    id              INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    type            VARCHAR(50) NOT NULL,
    serial_number   VARCHAR(100) NOT NULL UNIQUE,
    room_id         INT NOT NULL,
    status          VARCHAR(30),
    warranty_expiry DATE,
    purchase_date   DATE,
    CONSTRAINT fk_device_room
        FOREIGN KEY (room_id) REFERENCES room(id)
);

CREATE TABLE server (
    id               INT PRIMARY KEY,
    hostname         VARCHAR(150) NOT NULL,
    status           VARCHAR(30),
    last_maintenance DATE,
    ip_address       VARCHAR(45),
    os               VARCHAR(100),
    ram_size         INT,
    cpu              VARCHAR(100),
    CONSTRAINT fk_server_device
        FOREIGN KEY (id) REFERENCES device(id)
);

CREATE TABLE pc_case (
    id       INT PRIMARY KEY,
    os       VARCHAR(100),
    ram_size INT,
    cpu      VARCHAR(100),
    gpu      VARCHAR(100),
    CONSTRAINT fk_pccase_device
        FOREIGN KEY (id) REFERENCES device(id)
);

CREATE TABLE projector (
    id               INT PRIMARY KEY,
    resolution       VARCHAR(50),
    brightness       INT,
    supports_wireless BOOLEAN,
    CONSTRAINT fk_projector_device
        FOREIGN KEY (id) REFERENCES device(id)
);

CREATE TABLE router (
    id             INT PRIMARY KEY,
    ip_address     VARCHAR(45),
    mac_address    VARCHAR(17),
    status         VARCHAR(30),
    wifi_standards VARCHAR(100),
    max_speed      VARCHAR(50),
    CONSTRAINT fk_router_device
        FOREIGN KEY (id) REFERENCES device(id)
);

CREATE TABLE monitor (
    id           INT PRIMARY KEY,
    screen_size  NUMERIC(4,1),
    resolution   VARCHAR(50),
    panel_type   VARCHAR(50),
    refresh_rate INT,
    aspect_ratio VARCHAR(20),
    CONSTRAINT fk_monitor_device
        FOREIGN KEY (id) REFERENCES device(id)
);

CREATE TABLE laptop (
    id       INT PRIMARY KEY,
    os       VARCHAR(100),
    ram_size INT,
    cpu      VARCHAR(100),
    gpu      VARCHAR(100),
    CONSTRAINT fk_laptop_device
        FOREIGN KEY (id) REFERENCES device(id)
);

-- service bridge (IT desk servicing buildings)

CREATE TABLE service (
    service_id   INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    desk_id      INT NOT NULL,
    building_id  INT NOT NULL,
    service_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    service_type VARCHAR(50),
    status       VARCHAR(30),
    notes        TEXT,
    CONSTRAINT fk_service_desk
        FOREIGN KEY (desk_id) REFERENCES it_desk(id),
    CONSTRAINT fk_service_building
        FOREIGN KEY (building_id) REFERENCES building(id)
);


-- request (device issues, created & resolved by people)

CREATE TABLE request (
    id            INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    device_id     INT NOT NULL,
    time_created  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    time_resolved TIMESTAMP,
    created_by    INT NOT NULL,
    resolved_by   INT,
    priority      VARCHAR(20),
    rq_type       VARCHAR(50),
    status        VARCHAR(30),
    description   TEXT,
    comments      TEXT,
    CONSTRAINT fk_request_device
        FOREIGN KEY (device_id) REFERENCES device(id),
    CONSTRAINT fk_request_created_by
        FOREIGN KEY (created_by) REFERENCES person(person_id),
    CONSTRAINT fk_request_resolved_by
        FOREIGN KEY (resolved_by) REFERENCES it_technician(person_id)
);