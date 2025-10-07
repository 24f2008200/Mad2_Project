<template>
    <div class="container mt-4">
        <RowEditor title="Edit Profile" :row="profile" :fields="[
            { key: 'name', label: 'Name', type: 'text' },
            { key: 'email', label: 'Email', type: 'text' },
            { key: 'age', label: 'Age', type: 'number' }
        ]" @save="updateProfile" @cancel="closeModal"></RowEditor>
    </div>
</template>
